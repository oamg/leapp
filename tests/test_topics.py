import pytest

from leapp.exceptions import InvalidTopicDefinitionError
from leapp.topics import Topic, ErrorTopic, get_topics
import leapp.topics


class UnitTestTopic(Topic):
    name = "test-topic"


def test_topic():
    assert getattr(leapp.topics, 'TestTopic') is UnitTestTopic


def test_get_topics():
    topics = get_topics()
    assert len(topics) >= 2
    assert UnitTestTopic in topics
    assert ErrorTopic in topics
    UnitTestTopic.name = None
    with pytest.raises(InvalidTopicDefinitionError):
        get_topics()
