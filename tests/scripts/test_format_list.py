import pytest

from leapp.libraries.stdlib import FMT_LIST_SEPARATOR, format_list

SEP = ', '


@pytest.mark.parametrize('data, kwargs, expected', [
    # Basic usage
    ([], {}, ''),
    (['c', 'a', 'b'], {}, '{0}a{0}b{0}c'.format(FMT_LIST_SEPARATOR)),
    (['c', 'a', 'b'], {'sep': SEP}, ', a, b, c'),
    (['a'], {'sep': SEP}, ', a'),
    # Sorting
    (['c', 'a', 'b'], {'sep': SEP, 'callback_sort': None}, ', c, a, b'),
    (['c', 'a', 'b'], {'sep': SEP, 'callback_sort': lambda d: sorted(d, reverse=True)}, ', c, b, a'),
    # Limit
    (['c', 'a', 'b'], {'sep': SEP, 'limit': 2}, ', a, b'),
    (['c', 'a', 'b'], {'sep': SEP, 'limit': 0}, ', a, b, c'),
    (['b', 'a'], {'sep': SEP, 'limit': 10}, ', a, b'),
    (['c', 'a', 'b'], {'sep': SEP, 'limit': -1}, ', a, b, c'),
    # Non-list iterables
    ({'a', 'b', 'c'}, {'sep': SEP, 'limit': 2}, ', a, b'),
    (('a', 'b'), {'sep': SEP}, ', a, b'),
    ({'b': 1, 'a': 2}, {'sep': SEP}, ', a, b'),
    # Generators
    ((x for x in ['c', 'a', 'b']), {'sep': SEP}, ', a, b, c'),
    ((x for x in ['c', 'a', 'b']), {'sep': SEP, 'callback_sort': None, 'limit': 2}, ', c, a'),
], ids=[
    'empty_data',
    'single_item',
    'default_separator',
    'custom_separator',
    'no_sort',
    'reverse_sort',
    'limit',
    'limit_zero',
    'limit_larger_than_data',
    'negative_limit_ignored',
    'set_input',
    'tuple_input',
    'dict_keys_input',
    'generator_sorted',
    'generator_unsorted_with_limit',
])
def test_format_list(data, kwargs, expected):
    assert format_list(data, **kwargs) == expected
