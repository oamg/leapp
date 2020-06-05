from leapp.utils.deprecation import deprecated


@deprecated('2010-01-01', 'Deprecated class without __init__')
class DeprecatedNoInit(object):
    pass


@deprecated('2010-01-01', 'Deprecated class with __init__')
class DeprecatedWithInit(object):
    pass


@deprecated('2010-01-01', 'Deprecated base class without __init__')
class DeprecatedBaseNoInit(object):
    pass


class DeprecatedNoInitDerived(DeprecatedBaseNoInit):
    pass


@deprecated('2010-01-01', 'Deprecated base class with __init__')
class DeprecatedBaseWithInit(object):
    def __init__(self):
        pass


class DeprecatedWithInitDerived(DeprecatedBaseWithInit):
    def __init__(self):
        pass


@deprecated('2010-01-01', 'This function is no longer supported.')
def deprecated_function():
    pass
