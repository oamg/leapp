import sys

from leapp.exceptions import InvalidTagDefinitionError
from leapp.utils.meta import get_flattened_subclasses, with_metaclass


class TagMeta(type):
    def __new__(mcs, name, bases, attrs):
        klass = super(TagMeta, mcs).__new__(mcs, name, bases, attrs)
        if klass.__module__ is not TagMeta.__module__:
            setattr(sys.modules[mcs.__module__], name, klass)
            setattr(klass, 'actors', ())
            if not getattr(klass, 'parent', None):
                data = {'parent': klass, 'actors': ()}
                setattr(klass, 'Before', type('Before' + name, (Tag,), dict(name='before-' + klass.name, **data)))
                setattr(klass, 'After', type('After' + name, (Tag,), dict(name='after-' + klass.name, **data)))
                common = type('Common' + name, (Tag,), dict(name='common-' + klass.name, **data))
                data_common = {'parent': common, 'actors': ()}
                setattr(common, 'Before', type('BeforeCommon' + name, (Tag,),
                                               dict(name='before-' + common.name, **data_common)))
                setattr(common, 'After', type('AfterCommon' + name, (Tag,),
                                              dict(name='after-' + common.name, **data_common)))
                setattr(klass, 'Common', common)
        return klass


class Tag(with_metaclass(TagMeta)):
    pass


def get_tags():
    tags = get_flattened_subclasses(Tag)
    for tag in (tag for tag in tags if tag is not Tag):
        tag_name = getattr(tag, 'name', None)
        if not tag_name:
            raise InvalidTagDefinitionError('Tag {} does not contain a tag name attribute'.format(tag))
    return tags
