import os
import subprocess
import sys
import tempfile
import stat
import shutil

#TODO: Use ctypes.CDLL to issue mount / umount calls
#import ctypes
#_libc = ctypes.CDLL('libc.so.6')
#_umount = _libc.umount
#_mount = _libc.mount


def _create_devices(devpath, selinux=False):
    ''' Create special devices without which the jail wouldn't work

        :param devpath: Path where to create the devices
        :type devpath:  str
        :param selinux: Whether created devices should be labelled
        :type selinux:  bool
    '''
    # common access masks we're gonna need
    ownerrw = 0o600 | stat.S_IFCHR
    allrw = 0o666 | stat.S_IFCHR

    # table of actual device nodes we need to create
    device_list = (
        ('console', (5, 1), ownerrw, 'console_device_t'),
        ('full',    (1, 7), allrw,   'null_device_t'),
        ('null',    (1, 3), allrw,   'null_device_t'),
        ('tty',     (5, 0), allrw,   'devtty_t'),
        ('zero',    (1, 5), allrw,   'zero_device_t'),
        ('random',  (1, 8), allrw,   'random_device_t'),
        ('urandom', (1, 9), allrw,   'urandom_device_t'),
    )

    # table of /dev symlinks pointing somewhere into /proc
    links = (
        ('core',   '/proc/kcore'),
        ('fd',     '/proc/self/fd'),
        ('stdin',  '/proc/self/fd/0'),
        ('stdout', '/proc/self/fd/1'),
        ('stderr', '/proc/self/fd/2'),
    )

    # create devices
    for (name, (hi, lo), mode, label) in device_list:
        fullpath = os.path.join(devpath, name)
        os.mknod(
            fullpath,
            mode,
            os.makedev(hi, lo)
        )
        if selinux:
            subprocess.check_call(['chcon', '-t', label, fullpath])

    # create symlinks
    for (src, target) in links:
        fullpath = os.path.join(devpath, src)
        os.symlink(
            target,
            fullpath
        )
        if selinux:
            subprocess.check_call(['chcon', '-h', '-t', 'device_t', fullpath])


def _consume_pipe(r, w, buffer_size=0x1000):
    ''' Helper function for consuming data from pipes

        :param r: Read end of the pipe
        :type r:  int
        :param w: Write end of the pipe
        :type w:  int
        :param buffer_size: Size of the read buffer
        :type buffer_size: int
    '''
    # first close the write end since we're just going to read
    os.close(w)
    b = os.read(r, buffer_size)
    output = b
    while b:
        b = os.read(r, buffer_size)
    output += b
    # now close the read end as well
    os.close(r)
    return output


def call(*args, **kwargs):
    ''' This interface mimics :py:func:`subprocess.check_output`, however since
        we need to create mount namespace and use mount/umount system call this
        only makes sense as a root

    '''
    # directory for the jailed file system
    tempdir = tempfile.mkdtemp()

    # directory for devices that we need
    devdir = tempfile.mkdtemp()

    # location in `tempdir` where `devdir` will be bind mounted
    devpath = os.path.join(tempdir, 'dev')
    tmppath = os.path.join(tempdir, 'tmp')

    # capture our current working directory so that we can `cd` to it in the jailed process
    cwd = os.getcwd()

    nothrow = 'nothrow' in kwargs and kwargs['nothrow']
    if 'nothrow' in kwargs:
        del kwargs['nothrow']

    # create devices, directorie and mountpoints
    try:
        _create_devices(devdir)
        os.mkdir(tmppath)
        # TODO: Use the libc function
        # TODO: Include other mounts as well (/home ...)
        subprocess.check_call(['mount', '-o', 'ro', '--make-unbindable', '--bind', '/', tempdir])
        subprocess.check_call(['mount', '--bind', devdir, devpath])
        subprocess.check_call(['mount', '-t', 'tmpfs', '-o', 'size=10M', 'tmpfs', tmppath])
    except Exception as exc:
        # something went wrong during jail setup, remove directories we (may have) created
        shutil.rmtree(devdir)
        os.removedirs(tempdir)
        # reraise if explicitly asked to do so
        if not nothrow:
            raise exc
        return None

    # figure out if and what pipes we need to create for data exchange
    handle_out = 'stdout' in kwargs
    handle_err = 'stderr' in kwargs #TODO: inject logger here

    # if `stdout`/`stderr` is not provided, we need to buffer the output ourselves
    # so we create a pipe and pass the write end to the jailed child process
    if not handle_out:
        r, w = os.pipe()
        kwargs['stdout'] = w
    if not handle_err:
        re, we = os.pipe()
        kwargs['stderr'] = we

    if os.fork():
        # parent process

        # TODO: This absolutely must use select/poll on the r/re pipes and drain both
        #       of them at the same time to prevent stalls in case of a lot of traffic
        #       going through `stderr`
        #
        #       The problem with the current code is that if the executed
        #       application fills up `stderr` kernel buffer all writes will start
        #       be blocked and the application will be deadlocked
        if not handle_out:
            output = _consume_pipe(r, w)
        if not handle_err:
            err = _consume_pipe(re, we)

        # wait for the child process to finish before we tear down the jail
        _, status = os.wait()
        exitcode = (status >> 8) & 0xff
        try:
            # remove our mounts
            # TODO: Use the libc function
            subprocess.check_call(['umount', devpath])
            subprocess.check_call(['umount', tmppath])
            subprocess.check_call(['umount', tempdir])
            # remove temporary directory
            shutil.rmtree(tempdir)
        finally:
            shutil.rmtree(devdir)

        # something went wrong in our child process, return/raise appropriate error
        if exitcode:
            if not nothrow:
                raise subprocess.CalledProcessError(exitcode, args[0], output=err)
            elif not handle_err:
                return exitcode, err
            else:
                return exitcode, None

        return 0, output
    else:
        # child process

        # close read parts of the pipse
        if not handle_out:
            os.close(r)
        if not handle_err:
            os.close(re)

        # chroot into the jail and execute the command
        os.chroot(tempdir)

        # make sure our CWD points to correct inode
        os.chdir(cwd)

        try:
            # execute the command
            subprocess.check_call(*args, **kwargs)
        except subprocess.CalledProcessError as cpe:
            # exit child process with corresponding error code
            sys.exit(cpe.returncode)
        finally:
            if not handle_out:
                os.close(w)
            if not handle_err:
                os.close(we)

        # exit in a normal way now
        sys.exit(0)


print(call(['cat', '/etc/fedora-release']))
