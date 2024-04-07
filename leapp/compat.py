import gettext  # noqa: F401; pylint: disable=unused-import
import importlib
import locale
import sys


__all__ = ('string_types', 'IS_PYTHON2', 'IS_PYTHON3', 'httplib', 'unicode_type', 'raise_with_traceback')

IS_PYTHON2 = sys.version_info < (3,)
IS_PYTHON3 = not IS_PYTHON2

string_types = ()


# Python 2 code
if IS_PYTHON2:

    import httplib
    string_types = (str, globals()['__builtins__']['unicode'])
    unicode_type = string_types[1]
    from leapp.compatpy2only import raise_with_traceback
    builtins_dict = globals()['__builtins__']

    def gettext_setup(t):
        def us(u):
            if isinstance(u, globals()['__builtins__']['unicode']):
                return u
            return unicode_type(u)

        def singular(msg):
            return t.ugettext(us(msg))

        def plural(msg1, msg2, n):
            return t.ungettext(us(msg1), us(msg2), n)

        return singular, plural

    def setlocale(category, loc=None):
        locale.setlocale(category, loc.encode('utf-8') if loc else None)

# Python 3 code
else:
    import http.client as httplib
    import builtins
    string_types = (str,)
    unicode_type = str
    builtins_dict = builtins.__dict__

    def gettext_setup(t):
        singular = t.gettext
        plural = t.ngettext
        return singular, plural

    def setlocale(category, loc=None):
        locale.setlocale(category, loc)

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


def load_module(importer, name):
    """
    Loads a module using the given importer and module name

    :param importer: A finder implementation (returned by e.g. pkgutils.iter_modules)
    :param name: Module name
    :return: The loaded module
    """
    if sys.version_info < (3, 4):
        return importer.find_module(name).load_module(name)

    spec = importer.find_spec(name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
