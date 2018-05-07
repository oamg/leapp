import json
import os
import re

from leapp.exceptions import UsageError
from leapp.utils.clicmd import command_aware_wraps


def requires_project(f):
    """
    Decorator for snactor commands that require to be run in a project directory.
    """
    @command_aware_wraps(f)
    def checker(*args, **kwargs):
        if not find_project_basedir('.'):
            raise UsageError('This command must be executed from the project directory')
        return f(*args, **kwargs)
    return checker


def to_snake_case(name):
    """
    Converts a UpperCaseName to a snake_case_name

    :param name: Name to convert
    :return: converted snake case name
    """
    if '-' in name:
        name = ''.join([part.capitalize() for part in name.split('-') if part])
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def make_class_name(name):
    """
    Converts a snake_case_name to a UpperCaseName

    :param name: Name to convert
    :return: Converted class name
    """
    return ''.join(map(lambda x: x.capitalize(), to_snake_case(name).split('_')))


def make_name(name):
    """
    Converts a given name to lower case snake case

    :param name: Name to convert
    :return: Lower snake case
    """
    return to_snake_case(name)


def find_project_basedir(path):
    """
    Tries to find .leapp directory recursively ascending until it hits the root directory

    :param path: Path to start from (can be relative)
    :return: None if base directory was not found otherwise absolute path to the base directory
    """
    path = os.path.realpath(path)
    while True:
        if os.path.isdir(os.path.join(path, '.leapp')):
            return path
        path, current = os.path.split(path)
        if not current:
            return None


def get_project_metadata(path):
    """
    Gets the parsed meta data file as dictionary

    :param path: Path to start loading the meta data from (Can be anywhere within the repository it will use
                 :py:func:`find_project_dir` to find the project base directory)
    :return: Dictionary with the meta data or an empty dictionary
    """
    basedir = find_project_basedir(path)
    if basedir:
        with open(os.path.join(basedir, '.leapp', 'info'), 'r') as f:
            return json.load(f)
    return {}


def get_project_name(path):
    """
    Retrieves the project name from the project meta data from within the given path. (Can be anywhere within the
    repository it will use :py:func:`find_project_dir` to find the project base directory)
    :param path: Path within the leapp repository
    :return: Name of the repository
    :raises: KeyError if no name was found (e.g. not a valid repository path)
    """
    return get_project_metadata(path)['name']
