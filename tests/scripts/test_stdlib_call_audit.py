import os
import pytest
import six

from leapp.libraries.stdlib import run

CUR_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def adjust_cwd():
    previous_cwd = os.getcwd()
    os.chdir(os.path.join(CUR_DIR, "../"))
    yield
    os.chdir(previous_cwd)


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


def test_missing_executable(monkeypatch, adjust_cwd):  # no-qa: W0613; pylint: disable=unused-argument
    """
    In case the executable is missing.

    :return: Pass/Fail
    """
    def mocked_fork():
        # raise the generic exception as we want to prevent fork in this case
        # and want to bypass possible catch
        raise Exception()  # no-qa: W0719; pylint: disable=broad-exception-raised

    monkeypatch.setattr(os, 'fork', mocked_fork)
    with pytest.raises(OSError):
        run(['my-non-existing-exec-2023-asdf'])

    with pytest.raises(OSError):
        # this file is not executable, so even if it exists the OSError should
        # be still raised
        run(['panagrams'], env={'PATH': '../data/call_data/'})
