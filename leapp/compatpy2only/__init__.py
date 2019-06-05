RAISE_EXC_HELPER = '''
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
    raise exc, None, tb
    '''

exec(RAISE_EXC_HELPER, globals(), locals())  # noqa; pylint: disable=exec-used
