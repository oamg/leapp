import os
from leapp.utils.project import requires_project, to_snake_case, make_class_name, make_name, find_project_basedir,\
    get_project_name, get_project_metadata
from leapp.exceptions import UsageError

from helpers import TESTING_PROJECT_NAME
from helpers import project_dir  # noqa: F401; pylint: disable=unused-variable

import pytest


def setup_module(m):
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


@requires_project
def _test_project_dir_presence():
    pass


def test_requires_project(project_dir):
    with pytest.raises(UsageError):
        _test_project_dir_presence()
    with project_dir.as_cwd():
        _test_project_dir_presence()


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


def test_find_project_basedir(project_dir):
    nested = project_dir.mkdir('a').mkdir('b').mkdir('c')
    assert project_dir.samefile(find_project_basedir(nested.strpath))
    assert project_dir.samefile(find_project_basedir(project_dir.strpath))
    assert find_project_basedir('.') is None


def test_get_project_metadata(project_dir):
    assert get_project_name(project_dir.strpath) == TESTING_PROJECT_NAME
    assert get_project_metadata(project_dir.strpath)['name'] == TESTING_PROJECT_NAME
    assert not get_project_metadata('.')