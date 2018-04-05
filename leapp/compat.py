import sys


__all__ = ('string_types', 'IS_PYTHON2', 'IS_PYTHON3', 'httplib')

IS_PYTHON2 = sys.version_info < (3,)
IS_PYTHON3 = not IS_PYTHON2

string_types = ()


# Python 2 code
if IS_PYTHON2:

    import httplib
    string_types = (str, globals()['__builtins__']['unicode'])

# Python 3 code
else:

    import http.client as httplib
    string_types = (str,)
