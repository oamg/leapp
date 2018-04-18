import sys

from leapp.exceptions import InvalidTopicDefinitionError
from leapp.utils.meta import get_flattened_subclasses, with_metaclass


class TopicMeta(type):
    """
    Meta class for the registration of topics
    """

    def __new__(mcs, name, bases, attrs):
        klass = super(TopicMeta, mcs).__new__(mcs, name, bases, attrs)
        setattr(sys.modules[mcs.__module__], name, klass)
        setattr(klass, 'messages', ())
        return klass


class Topic(with_metaclass(TopicMeta)):
    """ Base class for all :ref:`topics <terminology:topic>`"""

    name = None
    """ Name of the topic """

    messages = ()
    """
    Tuple of :py:class:`leapp.models.Model` derived classes that are using this topic are automatically added to this
    variable.
    """


class ErrorTopic(Topic):
    """
    A special topic for errors during the execution.
    """
    name = 'errors'


def get_topics():
    """
    :return: All registered :py:class:`leapp.topics.Topic` derived classes
    """
    topics = get_flattened_subclasses(Topic)
    for topic in (topic for topic in topics):
        topic_name = getattr(topic, 'name', None)
        if not topic_name:
            raise InvalidTopicDefinitionError('Topic {} does not contain a name attribute'.format(topic))
    return topics
