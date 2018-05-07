from leapp.utils.meta import get_flattened_subclasses, with_metaclass

import pytest


def test_with_metaclass():
    class MetaClassCreated(Exception):
        pass

    class TestMetaClass(type):
        def __new__(mcs, name, bases, attrs):
            raise MetaClassCreated()

    with pytest.raises(MetaClassCreated):
        class MetaClassUser(with_metaclass(TestMetaClass)):
            pass


def test_get_flattened_subclasses():
    class BaseClass(object):
        pass

    class SubClass(BaseClass):
        pass

    class SubSubClass(SubClass):
        pass

    class SubSubSubClass(SubSubClass):
        pass

    classes = get_flattened_subclasses(BaseClass)
    assert len(classes) == 3
    assert SubClass in classes
    assert SubSubClass in classes
    assert SubSubSubClass in classes
