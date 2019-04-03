from leapp.libraries.stdlib.call import _call

import os
import pytest


_CALLBACKS = [{}, [], 'string', lambda v: None, lambda a, b, c: None, None]
_POSITIVE_INTEGERS = [[], {}, 'x', -21, 0, None, -2.1, False, True, 0.0]
_STDIN = [[], {}, 0.123, lambda: None]


def test_invalid_command():
    with pytest.raises(TypeError):
        _call('i should be a list or tuple really')


def test_stdin_string():
    ret = _call(('bash', '-c', 'read MSG; echo "<$MSG>"'), stdin='LOREM IPSUM')
    assert ret['stdout'] == '<LOREM IPSUM>\n'


def test_stdin_fd():
    r, w = os.pipe()
    # The string we write here should not exceed `/proc/sys/fs/pipe-max-size`
    # which represents the size of the kernel buffer backing the pipe
    os.write(w, b'LOREM IPSUM')
    os.close(w)
    ret = _call(('bash', '-c', 'read MSG; echo "<$MSG>"'), stdin=r)
    os.close(r)
    assert ret['stdout'] == '<LOREM IPSUM>\n'

# FIXME: (**LINE_BUFFER**)
# def test_linebuffer_callback():
#     buffered = []
#
#     def callback(fd, data):
#         buffered.append(data)
#     _call(('bash', '-c', 'echo 1; echo 2; echo 3'), callback_linebuffered=callback)
#     assert buffered == ['1', '2', '3']


@pytest.mark.parametrize('p', _STDIN)
def test_stdin_check(p):
    with pytest.raises(TypeError):
        _call(('true',), stdin=p)


def test_output_1():
    ret = _call(('false',))
    assert isinstance(ret['exit_code'], int)
    assert ret['exit_code'] == 1
    assert isinstance(ret['pid'], int)
    assert ret['pid'] > 0
    assert ret['stdout'] == ''
    assert ret['stderr'] == ''
    assert isinstance(ret['signal'], int)
    assert ret['signal'] == 0


def test_output_2():
    ret = _call(('bash', '-c', 'echo STDOUT; (exec >&2 ; echo STDERR); exit 42',))
    assert isinstance(ret['exit_code'], int)
    assert ret['exit_code'] == 42
    assert isinstance(ret['pid'], int)
    assert ret['pid'] > 0
    assert ret['stdout'] == 'STDOUT\n'
    assert ret['stderr'] == 'STDERR\n'
    assert isinstance(ret['signal'], int)
    assert ret['signal'] == 0


def test_env_injection():
    ret = _call(('bash', '-c', 'echo $TEST'), env={'TEST': 'SUCCESS'})
    assert isinstance(ret['exit_code'], int)
    assert ret['exit_code'] == 0
    assert ret['stdout'] == 'SUCCESS\n'


@pytest.mark.parametrize('p', _CALLBACKS)
def test_callability_check(p):
    with pytest.raises(TypeError):
        _call(('true',), callback_raw='nope')


# FIXME: (**LINE_BUFFER**)
# @pytest.mark.parametrize('p', _CALLBACKS)
# def test_callability_check(p):
#     with pytest.raises(TypeError):
#         _call(('true',), callback_linebuffered=p)


@pytest.mark.parametrize('p', _POSITIVE_INTEGERS)
def test_polltime(p):
    with pytest.raises(ValueError):
        _call(('true',), poll_timeout=p)


@pytest.mark.parametrize('p', _POSITIVE_INTEGERS)
def test_buffer_size(p):
    with pytest.raises(ValueError):
        _call(('true',), read_buffer_size=p)
