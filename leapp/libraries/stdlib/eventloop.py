from __future__ import print_function

import errno
import platform
import select
from collections import defaultdict

POLL_NULL = 0
POLL_IN = 1
POLL_PRI = 2
POLL_OUT = 4
POLL_ERR = 8
POLL_HUP = 16


class EventLoopKQUEUE(object):
    MAX_EVENTS = 1024

    def __init__(self):
        self._kqueue = select.kqueue()
        self._fds = {}

    def _control(self, fd, mode, flags):
        events = []
        if mode & POLL_OUT:
            events.append(select.kevent(fd, select.KQ_FILTER_WRITE, flags))
        if mode & POLL_IN:
            events.append(select.kevent(fd, select.KQ_FILTER_READ, flags))
        for e in events:
            try:
                self._kqueue.control([e], 0)
            except OSError as exc:
                if exc.errno not in (errno.EBADF, errno.ENOENT):
                    raise

    def poll(self, timeout):
        if timeout < 0:
            timeout = None  # kqueue behaviour
        events = self._kqueue.control(None, EventLoopKQUEUE.MAX_EVENTS, timeout)
        results = defaultdict(lambda: POLL_NULL)
        for e in events:
            fd = e.ident
            print(e)
            if e.flags & select.KQ_EV_EOF and e.data == 0:
                results[fd] = POLL_HUP
            elif e.filter == select.KQ_FILTER_READ:
                results[fd] |= POLL_IN
            elif e.filter == select.KQ_FILTER_WRITE:
                results[fd] |= POLL_OUT
        return results.items()

    def register(self, fd, mode):
        self._fds[fd] = mode
        self._control(fd, mode, select.KQ_EV_ADD)

    def unregister(self, fd):
        self._control(fd, self._fds[fd], select.KQ_EV_DELETE)
        del self._fds[fd]

    def modify(self, fd, mode):
        self.unregister(fd)
        self.register(fd, mode)

    def close(self):
        self._kqueue.close()

    @property
    def closed(self):
        return self._kqueue.closed


EventLoop = EventLoopKQUEUE if platform.system() == 'Darwin' else select.epoll
