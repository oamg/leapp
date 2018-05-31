""" Leapp Models

These packages provide an interface describing a message payload data structure in the form of Models.
Together with the :py:mod:`leapp.models.fields`, package models are defined.

Example::

    class Boom(Model):
        topic = SomeTopic
        reason = fields.String()

    class Foobar(Model):
        topic = SomeTopic
        baz = fields.List(fields.String(), default=[])
        boom = fields.Nested(Boom)

Now, the models can be used like this::

    f = Foobar(boom=Boom())
    f.boom.reason = "Example"
    f.baz.append("Add a string value to the list")
    from pprint import pprint
    pprint(f.dump())

"""
import sys

from leapp.models import fields

from leapp.exceptions import ModelDefinitionError
from leapp.utils.meta import get_flattened_subclasses, with_metaclass
from leapp.topics import Topic, ErrorTopic
from leapp.models.error_severity import ErrorSeverity


class ModelMeta(type):
    """
    ModelMeta is a metaclass used for Model

    It verifies the validity of attributes and registers the model as a message type with the :py:class:`Topic`.
    """
    def __new__(mcs, name, bases, attrs):
        klass = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)

        model_ref_cls = globals().get('_ModelReference')
        if name == '_ModelReference' or (model_ref_cls and issubclass(klass, model_ref_cls)):
            setattr(sys.modules[mcs.__module__], name, klass)
            return klass

        # Every model has to be bound to a topic except for the Model base class
        # Since it is using this class as meta class, we will dynamically get the class object from the globals
        model_cls = globals().get('Model')
        if model_cls and issubclass(klass, model_cls):
            topic = getattr(klass, 'topic', None)
            if not topic or not issubclass(topic, Topic):
                raise ModelDefinitionError('Missing topic in Model {}'.format(name))
            topic.messages = tuple(set(topic.messages + (klass,)))

        kls_attrs = {name: value for name, value in attrs.items() if isinstance(value, fields.Field)}
        klass.fields = kls_attrs.copy()

        setattr(sys.modules[mcs.__module__], name, klass)
        return klass

    def __init__(cls, name, bases, attrs):
        super(ModelMeta, cls).__init__(name, bases, attrs)


class Model(with_metaclass(ModelMeta)):
    """
    Model is a base class for all models.

    Models are defining the data structure of the payload of messages and the
    metadata required, such as a name and topic.
    """
    def __init__(self, init_method='from_initialization', **kwargs):
        super(Model, self).__init__()
        for field in type(self).fields.keys():
            getattr(type(self).fields[field], init_method)(kwargs, field, self)

    topic = None
    """
    `topic` has to be set to a subclass of :py:class:`leapp.topics.Topic`
    It defines the categorization of this model.
    """

    fields = None
    """
    `fields` contains a dictionary with all attributes of the py:class:`leapp.models.fields.Field` type in the class.

    Note: Dynamically added fields are ignored by the framework.
    """

    @classmethod
    def create(cls, data):
        """
        Create an instance of this class and use the data to initialize the fields within.

        :param data: Data to initialize the Model from deserialized data
        :type data: dict
        :return: Instance of this class
        """
        return cls(init_method='to_model', **data)

    def dump(self):
        """
        Dumps the data in the dictionary form that is safe to serialize to JSON.

        :return: dict with a builtin representation of the data that can be safely serialized to JSON
        """
        result = {}
        for field in type(self).fields.keys():
            type(self).fields[field].to_builtin(self, field, result)
        return result

    def __eq__(self, other):
        """
        Implementation for equality comparison of Model instances
        """
        return isinstance(other, type(self)) and \
            all(getattr(self, name) == getattr(other, name) for name in sorted(type(self).fields.keys()))


class ErrorModel(Model):
    topic = ErrorTopic

    message = fields.String(required=True)
    severity = fields.StringEnum(required=True, choices=ErrorSeverity.ALLOWED_VALUES, default=ErrorSeverity.ERROR)
    details = fields.String(required=True, allow_null=True, default=None)
    actor = fields.String(required=True)
    time = fields.DateTime(required=True)


def get_models():
    """
    Returns a list of all currently loaded subclasses of Model

    :return: List Model subclasses
    """
    return [model for model in get_flattened_subclasses(Model) if model is not issubclass(model, _ModelReference)]


class _ModelReference(Model):
    _referenced = None
    _resolved = None

    def __new__(cls, *args, **kwargs):
        return cls.resolve()(*args, **kwargs)

    @classmethod
    def create(cls, data):
        return cls.resolve()(init_method='to_model', **data)

    @classmethod
    def resolve(cls):
        if not cls._resolved:
            try:
                cls._resolved = globals()[cls._referenced]
            except KeyError:
                raise ModelDefinitionError('Undefined Model "{}"'.format(cls._referenced))
        return cls._resolved


def resolve_model_references():
    """
    Resolves all dynamically created model references. When importing a model that has not been loaded
    yet, a dynamic model reference is created. After loading all models, resolve_model_references
    must be called to ensure the consistency of the code.

    :return: None
    """
    for reference in get_flattened_subclasses(_ModelReference):
        reference.resolve()


def _module_ref(name):
    reference = type(name + "Reference", (_ModelReference,), {})
    reference._referenced = name
    return reference


def _patch_module_getitem():
    class ReferenceDict(object):
        def __init__(self, module):
            self.__dict__['_module'] = module

        def __setattr__(self, name, value):
            setattr(self._module, name, value)

        def __delattr__(self, name):
            delattr(self._module, name)

        def __getattr__(self, item):
            return getattr(self._module, item, None) or _module_ref(item)

    sys.modules[__name__] = ReferenceDict(sys.modules[__name__])


_patch_module_getitem()
