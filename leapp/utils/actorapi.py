import os
import socket

import requests
import requests.adapters
import requests.exceptions

try:
    import requests.packages.urllib3 as urllib3  # noqa # pylint: disable=consider-using-from-import
except ImportError:
    import urllib3


RequestException = requests.exceptions.RequestException
"""
Exceptions that are raised through the actor API, which is retrieved from :py:func:`get_actor_api`
"""
_session = None


class _LeappAPIConnection(urllib3.connection.HTTPConnection):
    def __init__(self, timeout=60):
        self.sock = None
        super(_LeappAPIConnection, self).__init__('localhost', timeout=timeout)
        self.timeout = timeout

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        socket_path = os.environ.get('LEAPP_ACTOR_API', '/tmp/actors.sock')
        sock.connect(socket_path)
        self.sock = sock


class _LeappAPIConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
    def __init__(self, timeout=60):
        super(_LeappAPIConnectionPool, self).__init__('localhost')
        self.timeout = timeout

    def _new_conn(self):
        return _LeappAPIConnection(self.timeout)


class _LeappAPIAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, timeout=60):
        super(_LeappAPIAdapter, self).__init__()
        self.timeout = timeout

    def get_connection(self, url, proxies=None):
        return _LeappAPIConnectionPool(timeout=self.timeout)

    def request_url(self, request, proxies):
        return request.path_url


def get_actor_api():
    """
    :return: An instance of the Leapp actor API session that is using :py:class:`requests.Session` over a
             UNIX domain socket
    """
    global _session
    if _session:
        return _session
    _session = requests.session()
    _session.adapters.clear()
    _session.mount('leapp://', _LeappAPIAdapter())
    return _session
