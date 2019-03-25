import os

from leapp.libraries.stdlib import call
from leapp.libraries.stdlib.config import is_debug, is_verbose


def test_check_single_line_output():
    a_command = ['echo', 'This a single line test!']
    assert call(a_command) == [u'This a single line test!']


def test_check_single_line_output_no_split():
    a_command = ['echo', 'This a single line No Split test!']
    assert call(a_command, split=False) == u'This a single line No Split test!\n'


def test_check_multiline_output():
    a_command = ['echo', 'This a multi-\nline test!']
    assert call(a_command) == [u'This a multi-', u'line test!']


def test_check_multiline_output_no_split():
    a_command = ['echo', 'This a multi-\nline No Split test!']
    assert call(a_command, split=False) == u'This a multi-\nline No Split test!\n'


def test_is_verbose(monkeypatch):
    matrix = (
        (('1', '1'), True),
        (('0', '1'), True),
        (('1', '0'), True),
        (('0', '0'), False),
        ((0, 1), False),
        ((1, 1), False),
        ((1, 0), False),
        ((0, 0), False),
        (('1', 0), True),
        ((0, '1'), True)
    )
    for (debug, verbose), expected in matrix:
        monkeypatch.setattr(os, 'environ', {'LEAPP_DEBUG': debug, 'LEAPP_VERBOSE': verbose})
        assert is_verbose() == expected


def test_is_debug(monkeypatch):
    matrix = (
        (('1', '1'), True),
        (('0', '1'), False),
        (('1', '0'), True),
        (('0', '0'), False),
        ((0, 1), False),
        ((1, 1), False),
        ((1, 0), False),
        ((0, 0), False),
        (('1', 0), True),
        ((0, '1'), False)
    )
    for (debug, verbose), expected in matrix:
        monkeypatch.setattr(os, 'environ', {'LEAPP_DEBUG': debug, 'LEAPP_VERBOSE': verbose})
        assert is_debug() == expected
