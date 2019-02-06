from __future__ import print_function

import select
import os
import sys


STDIN = 0
STDOUT = 1
STDERR = 2


def _multiplex(ep, read_fds, callback_raw, callback_linebuffered,
               encoding='utf-8', write=None, timeout=1, buffer_size=80):
    # Register the file descriptors (stdout + stderr) with the epoll object
    # so that we'll get notifications when data are ready to read
    for fd in read_fds:
        ep.register(fd, select.EPOLLIN | select.EPOLLPRI)

    # Register a write file descriptor
    if write:
        ep.register(write[0], select.EPOLLOUT)

    # Offset into the `write[1]` buffer where we should continue writing to stdin
    offset = 0

    # We need to keep track of which file descriptors have already been drained
    # because when running under `pytest` it seems that all `epoll` events are
    # received twice so using solely `ep.unregister(fd)` will not work
    hupped = set()
    # Total number of 'hupped' file descriptors we expect
    num_expected = len(read_fds) + (1 if write else 0)
    # Set up file-descriptor specific buffers where we'll buffer the output
    buf = {fd: bytes() for fd in read_fds}
    linebufs = {fd: '' for fd in read_fds}

    while not ep.closed and len(hupped) != num_expected:
        events = ep.poll(timeout)
        for fd, event in events:
            if event == select.EPOLLHUP:
                hupped.add(fd)
                ep.unregister(fd)
            if event & (select.EPOLLIN | select.EPOLLPRI) != 0:
                fd_type = read_fds.index(fd) + 1
                read = os.read(fd, buffer_size)
                callback_raw((fd, fd_type), read)
                linebufs[fd] += read.decode(encoding)
                while '\n' in linebufs[fd]:
                    pre, post = linebufs[fd].split('\n', 1)
                    linebufs[fd] = post
                    callback_linebuffered((fd, fd_type), pre)
                buf[fd] += read
            elif event == select.EPOLLOUT:
                # Write data to pipe, `os.write` returns the number of bytes written,
                # thus we need to offset
                wfd, data = write
                if fd in hupped:
                    continue
                offset += os.write(fd, data[offset:])
                if offset == len(data):
                    os.close(fd)
                    hupped.add(fd)
                    ep.unregister(fd)

    # Process leftovers from line buffering
    for (fd, lb) in linebufs.items():
        if lb:
            callback_linebuffered(read_fds.index(fd) + 1, lb)

    return buf


def _call(command, callback_raw=lambda fd, value: None, callback_linebuffered=lambda fd, value: None,
          encoding='utf-8', poll_timeout=1, read_buffer_size=80, stdin=None):
    """
        :param command: The command to execute
        :type command: list, tuple
        :param encoding: Decode output or encode input using this encoding
        :type encoding: str
        :param poll_timeout: Timeout used by epoll to wait certain amount of time for activity on file descriptors
        :type poll_timeout: int
        :param read_buffer_size: How much data are we going to read form the file descriptors each iteration.
                                 The default value of 80 chosen to correspond with suggested terminal line width
        :type read_buffer_size: int
        :param callback_raw: Callback executed on raw data (before decoding) as they are read from file descriptors
        :type callback_raw: (fd: int, buffer: bytes) -> None
        :param callback_linebuffered: Callback executed on decoded lines as they are read from the file descriptors
        :type callback_linebuffered: (fd, buffer) -> None
        :param stdin: String or a file descriptor that will be written to stdin of the child process
        :type stdin: int, str
    """
    if not isinstance(command, (list, tuple)):
        raise TypeError('command parameter has to be a list or tuple')
    if not callable(callback_raw) or callback_raw.__code__.co_argcount != 2:
        raise TypeError('callback_raw parameter has to be callable accepting 2 parameters')
    if not callable(callback_linebuffered) or callback_linebuffered.__code__.co_argcount != 2:
        raise TypeError('callback_linebuffered parameter has to be callable accepting 2 parameters')
    if not isinstance(poll_timeout, int) or isinstance(poll_timeout, bool) or poll_timeout <= 0:
        raise ValueError('poll_timeout parameter has to be integer greater than zero')
    if not isinstance(read_buffer_size, int) or isinstance(read_buffer_size, bool) or read_buffer_size <= 0:
        raise ValueError('read_buffer_size parameter has to be integer greater than zero')

    # Create a separate pipe for stdout/stderr
    #
    # The parent process is going to use the read-end of the pipes for reading child's
    # stdout/stderr, whereas the forked children process is going to use the write-end
    # of the pipes to pass data to parent
    stdout, wstdout = os.pipe()
    stderr, wstderr = os.pipe()

    # We allow stdin to be either a file descriptor (int) or a string and we need to handle
    # each of those cases differently
    #
    # The case where stdin is a file descriptor is simple -- we just need to dup2() the file
    # descriptor into the child process' stdin. If stdin is a string, though, the situation is
    # more complicated and we need to create another pipe and write the string to the pipe
    # in the _multiplex function
    fstdin, wstdin = None, None
    stdin_fd, stdin_str = False, False
    if isinstance(stdin, int):
        stdin_fd = True
    elif isinstance(stdin, str):
        stdin_str = True
        fstdin, wstdin = os.pipe()
    elif stdin is not None:
        raise TypeError('stdin has to be either a file descriptor or string, not "{!s}"'.format(type(stdin)))

    ep = select.epoll()
    pid = os.fork()
    if pid > 0:
        # Since pid > 0, we are in the parent process, so we have to close the write-end
        # file descriptors
        os.close(wstdout)
        os.close(wstderr)
        # Extra optional arguments for the `_multiplex` function
        extra = {}
        if stdin_str:
            # NOTE: We use the same encoding for encoding the stdin string as well which might
            # be suboptimal in certain cases -- there are two possible solutions:
            #  1) Rather than string require the `stdin` parameter to already be bytes()
            #  2) Add another parameter for stdin_encoding
            extra['write'] = (wstdin, stdin.encode(encoding))
            os.close(fstdin)

        read = _multiplex(
            ep,
            [stdout, stderr],
            callback_raw,
            callback_linebuffered,
            timeout=poll_timeout,
            buffer_size=read_buffer_size,
            encoding=encoding,
            **extra
        )

        # Wait for the child to finish
        pid, status = os.wait()
        ep.close()

        # The status variable is a 16 bit value, where the lower octet describes
        # the signal which killed the proces, and the upper octet is the exit code
        signal, exit_code = status & 0xff, status >> 8 & 0xff
        ret = {'signal': signal, 'exit_code': exit_code, 'pid': pid}
        if not encoding:
            ret.update({
                'stdout': read[stdout],
                'stderr': read[stderr]
            })
        else:
            ret.update({
                'stdout': read[stdout].decode(encoding),
                'stderr': read[stderr].decode(encoding)
            })
        return ret
    else:
        # We are in the child process, so we need to close the read-end of the pipes
        # and assign our pipe's file descriptors to stdout/stderr
        #
        # If `stdin` is specified as a file descriptor, we simply pass it as the stdin of the
        # child. In case `stdin` is specified as a string, we pass in the read end of our
        # stdin pipe
        if stdin_fd:
            os.dup2(stdin, STDIN)
        if stdin_str:
            os.close(wstdin)
            os.dup2(fstdin, STDIN)
        os.close(stdout)
        os.close(stderr)
        os.dup2(wstdout, STDOUT)
        os.dup2(wstderr, STDERR)
        os.execlp(command[0], *command)
