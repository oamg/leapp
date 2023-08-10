import os

import pytest

from helpers import TESTING_REPOSITORY_NAME
from leapp.exceptions import CommandError
from leapp.utils.repository import (
    requires_repository,
    to_snake_case,
    make_class_name,
    make_name,
    find_repository_basedir,
    get_repository_name,
    get_repository_metadata,
)


def setup_module():
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


@requires_repository
def _test_repository_dir_presence():
    pass


def test_requires_repository(repository_dir):
    with pytest.raises(CommandError):
        _test_repository_dir_presence()
    with repository_dir.as_cwd():
        _test_repository_dir_presence()


_SNAKE_CASE_CONVERSION_FIXTURES = (
    ("UpperNameCase", "upper_name_case"),
    ("snake_case_persists", "snake_case_persists"),
    ("Dash-Separated-Names", "dash_separated_names")
)


@pytest.mark.parametrize("param", _SNAKE_CASE_CONVERSION_FIXTURES)
def test_to_snake_case(param):
    assert to_snake_case(param[0]) == param[1]


_MAKE_CLASS_NAME_CONVERSION_FIXTURES = (
    ("UpperNameCase", "UpperNameCase"),
    ("snake_case_modified", "SnakeCaseModified"),
    ("Dash-Separated-Names", "DashSeparatedNames"),
    ("dash-separated-names-lower", "DashSeparatedNamesLower"),
)


@pytest.mark.parametrize("param", _MAKE_CLASS_NAME_CONVERSION_FIXTURES)
def test_make_class_name(param):
    assert make_class_name(param[0]) == param[1]


@pytest.mark.parametrize("param", _SNAKE_CASE_CONVERSION_FIXTURES)
def test_make_name(param):
    assert make_name(param[0]) == param[1]


def test_find_repository_basedir(repository_dir):
    nested = repository_dir.mkdir('a').mkdir('b').mkdir('c')
    assert repository_dir.samefile(find_repository_basedir(nested.strpath))
    assert repository_dir.samefile(find_repository_basedir(repository_dir.strpath))
    assert find_repository_basedir('.') is None


def test_get_repository_metadata(repository_dir):
    assert get_repository_name(repository_dir.strpath) == TESTING_REPOSITORY_NAME
    assert get_repository_metadata(repository_dir.strpath)['name'] == TESTING_REPOSITORY_NAME
    assert not get_repository_metadata('.')
