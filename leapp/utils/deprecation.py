import datetime
import functools
import inspect
import warnings
from collections import namedtuple

from leapp.models import Model


_suppressed_deprecations = set()


def suppress_deprecation(*suppressed_items):
    """
    Decorator to suppress deprecation warnings during the execution of the decorated entity.

    This can be used directly on Actor classes OR functions. This relies on the fact that a class has a `process`
    method, if the method does not exist the ValueError exeption is raised.

    :param suppressed_items: Variable number of arguments each for entities to suppress the deprecation warnings for.
    """
    def decorator(item):
        target_item = item
        if inspect.isclass(item):
            target_item = getattr(item, 'process', None)
            if target_item is None:
                raise ValueError(
                    'The suppress_deprecation decorator has been used on a class which'
                    ' does not contain the process method. The decorator can be used'
                    ' only for classes with that method (e.g. classes derived from Actor).'
                    ' Use the decorator on the affected methods instead of the current class.'
                )

        @functools.wraps(target_item)
        def process_wrapper(*args, **kwargs):
            # we need to remove later just items that we add right now
            # added_items == new items we add now to ...
            added_items = set(suppressed_items) - _suppressed_deprecations
            _suppressed_deprecations.update(added_items)
            try:
                return target_item(*args, **kwargs)
            finally:
                # remove the added items
                _suppressed_deprecations.difference_update(added_items)
        if inspect.isclass(item):
            item.process = process_wrapper
            return item
        return process_wrapper
    return decorator


class _LeappDeprecationWarning(DeprecationWarning):
    since = None
    message = None


def deprecated(since, message, stack_level_offset=0):
    """
    `deprecated` is a decorator for items to mark them as being deprecated

    :param message: Information about why it was deprecated and potentially a pointer for an alternative
    :param since: Date since when this item is marked deprecated
    :type since: str in the form YYYY-MM-DD (strftime format: %Y-%m-%d)
    :param stack_level_offset: Number of stack levels to report above the reported stack level. This is mainly useful,
                               when using the decorator on a base class and ensuring the derived classes are going to
                               report deprecation usage at the place the derived class was intantiated and not in the
                               constructor of the derived class.
    :type stack_level_offset: int
    """
    # Ensure %Y-%m-%d format otherwise it will raise a Value error
    since = datetime.datetime.strptime(since, "%Y-%m-%d").date().strftime("%Y-%m-%d")

    def decorator(item):
        kind = 'function'
        if inspect.isclass(item):
            if issubclass(item, Model):
                kind = 'Model'
            else:
                kind = 'class'

        _since = since

        class _DeprecationWarningContext(_LeappDeprecationWarning):
            since = _since
            msg = message

        item.__deprecation__ = namedtuple('Deprecation', ('since', 'message'))(since=since, message=message)

        # Storing the result so we can suppress later the actual thing.
        # In case it is a class, the class itself is returned, so no problem here, however if we want to suppress
        # the usage of a function, we need to check against the wrapper
        result = None

        def do_warn():
            if result in _suppressed_deprecations:
                return

            # Inserts temporarily a filter rule
            warnings.simplefilter(action='always', category=_LeappDeprecationWarning)
            # Issue warning
            warnings.warn(message='Usage of deprecated {kind} "{name}"'.format(
                kind=kind, name=item.__name__), category=_DeprecationWarningContext, stacklevel=3 + stack_level_offset)
            # Pops temporarily inserted filtration rule
            warnings.filters.pop(0)

        if inspect.isclass(item):
            old_init = item.__init__

            @functools.wraps(item.__init__, assigned=('__name__', '__doc__'))
            def wrapper(*args, **kwargs):
                do_warn()
                return old_init(*args, **kwargs)
            item.__init__ = wrapper
            result = item
        else:
            @functools.wraps(item)
            def wrapper(*args, **kwargs):
                do_warn()
                return item(*args, **kwargs)
            result = wrapper
        return result
    return decorator
