import sys

from leapp.exceptions import InvalidTagDefinitionError
from leapp.utils.meta import get_flattened_subclasses, with_metaclass


class TagMeta(type):
    """
    Meta class for the registration of tags

    This meta class adds dynamically Common, Before, Before.Common, After and After.Common attributes to the
    tag class. For more information see :py:class:`leapp.tags.Tag`
    """
    def __new__(mcs, name, bases, attrs):
        klass = super(TagMeta, mcs).__new__(mcs, name, bases, attrs)
        if klass.__module__ is not TagMeta.__module__:
            setattr(sys.modules[mcs.__module__], name, klass)
            setattr(klass, 'actors', ())

            if not getattr(klass, 'parent', None):
                data = {'parent': klass, 'actors': ()}
                before_common = type('_' + name + 'BeforeCommon', (Tag,), dict(name='common-before-' + klass.name,
                                                                               **data))
                after_common = type('_' + name + 'AfterCommon', (Tag,), dict(name='common-after-' + klass.name, **data))
                klass.Before = type('_' + 'Before' + name, (Tag,),
                                    dict(name='before-' + klass.name, Common=before_common, **data))
                klass.After = type('_' + 'After' + name, (Tag,),
                                   dict(name='after-' + klass.name, Common=after_common, **data))
                klass.Common = type('_' + 'Common' + name, (Tag,), dict(name='common-' + klass.name, **data))

                # To allow pickle to handle these tags we have to publish them on module level
                globals().update({
                    before_common.__name__: before_common,
                    after_common.__name__: after_common,
                    klass.Before.__name__: klass.Before,
                    klass.After.__name__: klass.After,
                    klass.Common.__name__: klass.Common})
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
    Tuple of all registered actors using this tag
    """


def get_tags():
    """
    :return: All registered :py:class:`leapp.tags.Tag` derived classes
    """
    tags = get_flattened_subclasses(Tag)
    for tag in (tag for tag in tags if tag is not Tag):
        tag_name = getattr(tag, 'name', None)
        if not tag_name:
            raise InvalidTagDefinitionError('Tag {} does not contain a tag name attribute'.format(tag))
    return tags
