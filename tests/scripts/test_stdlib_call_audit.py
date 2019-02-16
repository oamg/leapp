import pytest

from leapp.libraries.stdlib import run


def test_invalid_command():
    with pytest.raises(TypeError):
        run('i should be a list or tuple really')
