import os
import pytest

from leapp.libraries.stdlib import CalledProcessError, run
from leapp.libraries.stdlib.config import is_debug, is_verbose


_STDIN = [[], {}, 0.123, lambda: None]


def test_check_single_line_output():
    cmd = ['echo', 'This a single line test!']
    assert run(cmd, split=True)['stdout'] == [u'This a single line test!']


def test_check_single_line_output_no_split():
    cmd = ['echo', 'This a single line No Split test!']
    assert run(cmd, split=False)['stdout'] == u'This a single line No Split test!\n'


def test_check_multiline_output():
    cmd = ['echo', 'This a multi-\nline test!']
    assert run(cmd, split=True)['stdout'] == [u'This a multi-', u'line test!']


def test_check_multiline_output_no_split():
    cmd = ['echo', 'This a multi-\nline No Split test!']
    assert run(cmd, split=False)['stdout'] == u'This a multi-\nline No Split test!\n'


def test_check_error():
    cmd = ['false']
    with pytest.raises(CalledProcessError):
        run(cmd, checked=True)


def test_check_error_no_checked():
    cmd = ['false']
    assert run(cmd, checked=False)['exit_code'] == 1


def test_stdin_string():
    ret = run(('bash', '-c', 'read MSG; echo "<$MSG>"'), stdin='LOREM IPSUM')
    assert ret['stdout'] == '<LOREM IPSUM>\n'


def test_stdin_fd():
    r, w = os.pipe()
    # The string we write here should not exceed `/proc/sys/fs/pipe-max-size`
    # which represents the size of the kernel buffer backing the pipe
    os.write(w, b'LOREM IPSUM')
    os.close(w)
    ret = run(('bash', '-c', 'read MSG; echo "<$MSG>"'), stdin=r)
    os.close(r)
    assert ret['stdout'] == '<LOREM IPSUM>\n'


@pytest.mark.parametrize('p', _STDIN)
def test_stdin_check(p):
    with pytest.raises(TypeError):
        run(('true',), stdin=p)


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
