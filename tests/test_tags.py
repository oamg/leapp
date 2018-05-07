import pytest

from leapp.exceptions import InvalidTagDefinitionError
from leapp.tags import Tag, get_tags


class TestTag(Tag):
    name = "test-tag"


def test_tag_members_correctly_set():
    assert hasattr(TestTag, 'Common') and TestTag.Common.name == 'common-test-tag'
    assert hasattr(TestTag, 'Before') and TestTag.Before.name == 'before-test-tag'
    assert hasattr(TestTag.Before, 'Common') and TestTag.Before.Common.name == 'common-before-test-tag'
    assert hasattr(TestTag, 'After') and TestTag.After.name == 'after-test-tag'
    assert hasattr(TestTag.After, 'Common') and TestTag.After.Common.name == 'common-after-test-tag'
    assert not hasattr(TestTag.Common, 'Common')
    assert not hasattr(TestTag.Common, 'After')
    assert not hasattr(TestTag.Common, 'Before')
    assert not hasattr(TestTag.After, 'Before')
    assert not hasattr(TestTag.After, 'After')
    assert not hasattr(TestTag.Before, 'Before')
    assert not hasattr(TestTag.Before, 'After')
    assert not TestTag.actors
    assert not TestTag.Common.actors
    assert not TestTag.Before.actors
    assert not TestTag.After.actors
    assert not TestTag.Before.Common.actors
    assert not TestTag.After.Common.actors
    assert not hasattr(TestTag, 'parent')
    assert TestTag.Common.parent is TestTag
    assert TestTag.Before.parent is TestTag
    assert TestTag.After.parent is TestTag
    assert TestTag.Before.Common.parent is TestTag
    assert TestTag.After.Common.parent is TestTag


def test_get_tags():
    tags = get_tags()
    assert len(tags) % 6 == 0
    assert TestTag in tags
    assert TestTag.Common in tags
    assert TestTag.Before in tags
    assert TestTag.After in tags
    assert TestTag.Before.Common in tags
    assert TestTag.After.Common in tags
    TestTag.name = None
    with pytest.raises(InvalidTagDefinitionError):
        get_tags()
