import itertools


def with_metaclass(meta_class, base_class=object):
    """
    :param meta_class: The desired metaclass to use
    :param base_class: The desired base class to use, the default one is object
    :type base_class: Type
    :return: Metaclass type to inherit from

    :Example:

    .. code-block:: python

       class MyMetaClass(type):
           def __new__(mcs, name, bases, attrs):
               klass = super(MyMetaClass, mcs).__new__(mcs, name, bases, attrs)
               klass.added = "Added field"
               return klass

       class MyClass(with_metaclass(MyMetaClass)):
           pass

       # This is equivalent to python 2:
       class MyClass(object):
           __metaclass__ = MyMetaClass

       # Or python 3
       class MyClass(object, metaclass=MyMetaClass):
           pass
    """
    return meta_class(
        'with_meta_base_' + base_class.__name__ + '_' + meta_class.__name__,
        (base_class,),
        {}
    )


def get_flattened_subclasses(cls):
    """
    Returns all the given subclasses and their subclasses recursively for the given class
    :param cls: Class to check
    :type cls: Type
    :return: Flattened list of subclasses and their subclasses
    """
    classes = cls.__subclasses__()
    return list(itertools.chain(classes, *[get_flattened_subclasses(x) for x in classes]))
