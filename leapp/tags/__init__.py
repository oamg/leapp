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
                before_common = type(name + 'BeforeCommon', (Tag,), dict(name='common-before-' + klass.name, **data))
                after_common = type(name + 'AfterCommon', (Tag,), dict(name='common-after-' + klass.name, **data))
                klass.Before = type('Before' + name, (Tag,),
                                    dict(name='before-' + klass.name, Common=before_common, **data))
                klass.After = type('After' + name, (Tag,),
                                   dict(name='after-' + klass.name, Common=after_common, **data))
                klass.Common = type('Common' + name, (Tag,), dict(name='common-' + klass.name, **data))
        return klass


class Tag(with_metaclass(TagMeta)):
    """
    Tag is the base class for all Tags. Tags are used as filtering mechanism for actors to be loaded during workflow
    executions. Phases do use tags to filter actors according to their tags.

    Special Tag class attributes:
        Tag here refers to the derived class of Tag

        Tag.Common:
            Dynamically created class type that designates actors to be executed in the `main` stage during
            workflow phases. Using common includes this actor in any workflow, which means the that any workflow
            tag filter will be ignored if this tag matches.

        Tag.Before:
            Dynamically created class type that designates actors to be executed in the `before` stage during
            workflow phases.

        Tag.Before.Common:
            Dynamically created class type that designates actors to be executed in the `before` stage during
            workflow phases. Using common includes this actor in any workflow, which means the that any workflow
            tag filter will be ignored if this tag matches.

        Tag.After:
            Dynamically created class type that designates actors to be executed in the `after` stage during
            workflow phases.

        Tag.After.Common:
            Dynamically created class type that designates actors to be executed in the `after` stage during
            workflow phases. Using common includes this actor in any workflow, which means the that any workflow
            tag filter will be ignored if this tag matches.
    """

    actors = ()
    """
    Here are all actors registered that use this tag
    """


def get_tags():
    tags = get_flattened_subclasses(Tag)
    for tag in (tag for tag in tags if tag is not Tag):
        tag_name = getattr(tag, 'name', None)
        if not tag_name:
            raise InvalidTagDefinitionError('Tag {} does not contain a tag name attribute'.format(tag))
    return tags
