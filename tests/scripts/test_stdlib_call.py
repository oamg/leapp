import functools
import os
import pytest

from leapp.libraries.stdlib.call import _call


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


def test_linebuffer_callback():
    buffered = []

    def callback(fd, data):  # noqa; pylint: disable=unused-argument
        buffered.append(data)
    _call(('bash', '-c', 'echo 1; echo 2; echo 3'), callback_linebuffered=callback)
    assert buffered == ['1', '2', '3']


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


def test_env_preservation():
    os.environ['TEST'] = 'FAILURE'
    ret = _call(('bash', '-c', 'echo $TEST'), env={'TEST': 'SUCCESS', 'TEST2': 'HELLO_WORLD'})
    assert isinstance(ret['exit_code'], int)
    assert ret['exit_code'] == 0
    assert 'TEST2' not in os.environ
    assert os.environ['TEST'] == 'FAILURE'
    assert ret['stdout'] == 'SUCCESS\n'


def test_callability_check():
    with pytest.raises(TypeError):
        _call(('true',), callback_raw='nope')


@pytest.mark.parametrize('p', _CALLBACKS)
def test_callability_check_buffered(p):
    with pytest.raises(TypeError):
        _call(('true',), callback_linebuffered=p)


@pytest.mark.parametrize('p', _POSITIVE_INTEGERS)
def test_polltime(p):
    with pytest.raises(ValueError):
        _call(('true',), poll_timeout=p)


@pytest.mark.parametrize('p', _POSITIVE_INTEGERS)
def test_buffer_size(p):
    with pytest.raises(ValueError):
        _call(('true',), read_buffer_size=p)


class ArrayTracer(object):
    def __init__(self):
        self.value = []

    def __call__(self, unused, value):
        self.value.append(value)


def test_utf8_panagrams():
    panagrams_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'call_data',
        'panagrams'
    )

    with open(panagrams_path, 'rb') as f:
        p_raw = f.read()
        panagrams = p_raw.decode('utf-8')

    primes = [
        2, 3, 5, 7, 11, 13, 17, 19,
        23, 29, 31, 37, 41, 43, 47, 53, 59,
        61, 67, 71, 73, 79, 83, 89, 97,
        101, 103, 107, 109, 113
    ]

    for prime in primes:
        _lines, _raw = ArrayTracer(), ArrayTracer()
        r = _call(
            ('cat', panagrams_path,), read_buffer_size=prime,
            callback_linebuffered=_lines, callback_raw=_raw
        )
        assert r['stdout'] == panagrams
        assert panagrams.splitlines() == _lines.value
        assert p_raw == bytes(functools.reduce(lambda x, xs: x + xs, _raw.value, bytes()))
