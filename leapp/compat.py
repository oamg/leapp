import sys


__all__ = ('string_types', 'IS_PYTHON2', 'IS_PYTHON3', 'httplib')

IS_PYTHON2 = sys.version_info < (3,)
IS_PYTHON3 = not IS_PYTHON2

string_types = ()


# Python 2 code
if IS_PYTHON2:

    import httplib
    string_types = (str, globals()['__builtins__']['unicode'])
    from leapp.compatpy2only import raise_with_traceback

# Python 3 code
else:

    import http.client as httplib
    string_types = (str,)

    def raise_with_traceback(exc, tb):
        """
        This is a helper function to raise exceptions with a traceback.

        This is function is required to workaround the syntax changes between Python 2 and 3
        Python 3.4 introduced a with_traceback method to Exception classes and Python 3 removed the syntax
        which used to be used in Python 2.

        :param exc: Exception to raise
        :param tb:  Traceback to use
        :return: Nothing
        """
        raise exc.with_traceback(tb)
