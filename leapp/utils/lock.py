import os
import fcntl
import logging

from leapp.config import get_config
from leapp.exceptions import ProcessLockError


def leapp_lock(lockfile=None):
    return ProcessLock(lockfile=lockfile)


def _acquire_lock(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _clear_lock(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)


def _read_pid(fd):
    return os.read(fd, 20)


def _write_pid(fd, pid):
    _clear_lock(fd)
    os.write(fd, str(pid).encode('utf-8'))


class ProcessLock(object):

    def __init__(self, lockfile=None):
        self.log = logging.getLogger('leapp.utils.lock')
        self.lockfile = lockfile if lockfile else get_config().get('lock', 'path')

        self.fd = None

    def _get_pid_from_lockfile(self):
        running_pid = _read_pid(self.fd)
        self.log.debug("_get_pid_from_lockfile: running_pid=%s", running_pid)
        running_pid = int(running_pid)

        return running_pid

    def _try_lock(self, pid):
        if not _acquire_lock(self.fd):
            try:
                running_pid = self._get_pid_from_lockfile()
            except ValueError:
                process_msg = ''
            else:
                process_msg = ' by process with PID {}'.format(running_pid)

            msg = (
                'Leapp is currently locked{} and cannot be started.\n'
                'Please ensure no other instance of leapp is running and then delete the lockfile at {} and try again.'
            ).format(process_msg, self.lockfile)
            raise ProcessLockError(msg)

        try:
            _write_pid(self.fd, pid)
        except OSError:
            raise ProcessLockError('Could not write PID to lockfile.')

    def __enter__(self):
        my_pid = os.getpid()

        self.fd = os.open(self.lockfile, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            self._try_lock(my_pid)
        except ProcessLockError:
            os.close(self.fd)
            raise

    def __exit__(self, *exc_args):
        _clear_lock(self.fd)
        os.close(self.fd)
        os.unlink(self.lockfile)
