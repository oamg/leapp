import re
import socket


def decorate_getfqdn(fn):
    def wrap(*args, **kwargs):
        result = fn(*args, **kwargs)
        # check whether FQDN conforms to standard, see HOSTNAME(7)
        pattern = r"^(([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])\.)*([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$"
        if re.match(pattern, result, re.IGNORECASE):
            return result
        return 'invalid.hostname'

    return wrap


def apply_workaround():
    setattr(socket, 'getfqdn', decorate_getfqdn(socket.getfqdn))
