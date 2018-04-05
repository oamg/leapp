""" Leapp Models

This packages provides an interface to describe message payload data structure in the form of Models.
Together with the :py:mod:`leapp.models.fields` package models are defined.

Example::

    class Boom(Model):
        topic = SomeTopic
        reason = fields.String()

    class Foobar(Model):
        topic = SomeTopic
        baz = fields.List(fields.String(), default=[])
        boom = fields.Nested(Boom)

Now the models can be used like this::

    f = Foobar(boom=Boom())
    f.boom.reason = "Example"
    f.baz.append("Add a string value to the list")
    from pprint import pprint
    pprint(f.dump())

"""
import sys

from . import fields

from leapp.exceptions import ModelDefinitionError
from leapp.utils.meta import get_flattened_subclasses, with_metaclass
from leapp.topics import Topic, ErrorTopic


class ModelMeta(type):
    """
    ModelMeta is the meta class used for Model

    It verifies the validity of attributes and registers the model as message type with the :py:class:`Topic`
    """
    def __new__(mcs, name, bases, attrs):
        klass = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)

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
    Model is the base class for all models

    Models are defining the data structure of the payload of messages and the
    meta data required around that. Such as name and topic
    """
    def __init__(self, init_method='from_initialization', **kwargs):
        super(Model, self).__init__()
        for field in type(self).fields.keys():
            getattr(type(self).fields[field], init_method)(kwargs, field, self)

    topic = None
    """
    `topic` has to be set to a subclass of leapp.topics.Topic
    It defines the categorization of this model.
    """

    fields = None
    """
    `fields` contains a dictionary with all attributes of type `Field` in the class
    
    Note: Dynamically added fields are ignored by the framework
    """

    @classmethod
    def create(cls, data):
        """
        Create an instance of this class and use data to initialize the fields within

        :param data: Data to initialize the Model from deserialized data
        :type data: dict
        :return: Instance of this class
        """
        return cls(init_method='to_model', **data)

    def dump(self):
        """
        Dumps the data in dictionary form that is safe to serialize to JSON

        :return: dict with builtin representation of the data that can be safely serialized to JSON
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
    actor = fields.String(required=True)
    time = fields.DateTime(required=True)


def get_models():
    """
    Returns a list of all currently loaded subclasses of Model

    :return: List Model subclasses
    """
    return get_flattened_subclasses(Model)
