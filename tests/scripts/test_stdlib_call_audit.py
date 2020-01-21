import pytest
import six

from leapp.libraries.stdlib import run


def test_invalid_command():
    """
    Test raising TypeError when the command is not a tuple or list.

    :return: Pass/Fail
    """
    with pytest.raises(TypeError):
        run('i should be a list or tuple really')


def test_split():
    """
    Test the output lines are split into lists.

    :return: Pass/Fail
    """
    cmd = ['ls']
    result = run(cmd, split=True)
    assert isinstance(result['stdout'], list)
    assert len(result['stdout']) > 1


def test_no_encoding():
    """
    Test the output is base64 encoded after getting binary data

    :return: Pass/Fail
    """
    cmd = ['echo', '-n', '-e', '\\xeb']
    result = run(cmd, encoding=None)
    assert isinstance(result['stdout'], six.binary_type)
