import sys

from leapp.exceptions import InvalidTopicDefinitionError
from leapp.utils.meta import get_flattened_subclasses, with_metaclass


class TopicMeta(type):
    def __new__(mcs, name, bases, attrs):
        klass = super(TopicMeta, mcs).__new__(mcs, name, bases, attrs)
        setattr(sys.modules[mcs.__module__], name, klass)
        setattr(klass, 'messages', ())
        return klass


class Topic(with_metaclass(TopicMeta)):
    pass


class ErrorTopic(Topic):
    name = 'errors'


def get_topics():
    topics = get_flattened_subclasses(Topic)
    for topic in (topic for topic in topics):
        topic_name = getattr(topic, 'name', None)
        if not topic_name:
            raise InvalidTopicDefinitionError('Topic {} does not contain a name attribute'.format(topic))
    return topics
