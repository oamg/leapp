import errno
import json
import os
import re
import subprocess
import uuid

from leapp.exceptions import CommandError
from leapp.utils.clicmd import command_aware_wraps


def requires_repository(f):
    """
    Decorator for snactor commands that require to be run in a repository directory.
    """
    @command_aware_wraps(f)
    def checker(*args, **kwargs):
        if not find_repository_basedir('.'):
            raise CommandError('This command must be executed from the repository directory.')
        return f(*args, **kwargs)
    return checker


def to_snake_case(name):
    """
    Converts an UpperCaseName to a snake_case_name

    :param name: Name to convert
    :return: converted snake case name
    """
    if '-' in name:
        name = ''.join([part.capitalize() for part in name.split('-') if part])
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def make_class_name(name):
    """
    Converts a snake_case_name to an UpperCaseName

    :param name: Name to convert
    :return: Converted class name
    """
    return ''.join(map(lambda x: x.capitalize(), to_snake_case(name).split('_')))


def make_name(name):
    """
    Converts a given name to a lower snake case

    :param name: Name to convert
    :return: Lower snake case
    """
    return to_snake_case(name)


def find_repository_basedir(path):
    """
    Tries to find the .leapp directory recursively ascending until it hits the root directory

    :param path: Path to start from (can be relative)
    :return: None if the base directory was not found, otherwise the absolute path to the base directory
    """
    path = os.path.realpath(path)
    while True:
        if os.path.isdir(os.path.join(path, '.leapp')):
            return path
        path, current = os.path.split(path)
        if not current:
            return None


def get_repository_metadata(path):
    """
    Gets the parsed metadata file as a dictionary

    :param path: Path to start loading the metadata from (it can be anywhere within the repository it will use
                 :py:func:`find_repository_dir` to find the repository base directory)
    :return: Dictionary with the metadata or an empty dictionary
    """
    basedir = find_repository_basedir(path)
    if basedir:
        with open(os.path.join(basedir, '.leapp', 'info'), 'r') as f:
            return json.load(f)
    return {}


def get_repository_name(path):
    """
    Retrieves the repository name from the repository metadata from within the given path. (it can be anywhere within
    the repository it will use :py:func:`find_repositoryt_dir` to find the repository base directory)
    :param path: Path within the leapp repository
    :return: Name of the repository
    :raises: KeyError if no name was found (e.g. not a valid repository path)
    """
    return get_repository_metadata(path)['name']


def _create_and_set_repository_id(path):
    data = get_repository_metadata(path)
    if data:
        basedir = find_repository_basedir(path)
        data['id'] = str(uuid.uuid4())
        with open(os.path.join(basedir, '.leapp', 'info'), 'w') as f:
            json.dump(data, f)
    return data.get('id')


def get_repository_links(path):
    """
    Retrieves a list of repository ids that are linked to given repository.

    :param path: Path within the leapp repository
    :return: List of repository ids this repository is linked to
    """
    return get_repository_metadata(path).get('repos', [])


def add_repository_link(path, repo_id):
    """
    Add a link from another repository to the current repository.

    :param path: Path within the leapp repository to modify
    :param repo_id: UUIDv4 string identifier for the repository to link
    :param repo_id: str
    :return: None
    """
    data = get_repository_metadata(path)
    if data and repo_id != data['id']:
        basedir = find_repository_basedir(path)
        data.setdefault('repos', []).append(repo_id)
        with open(os.path.join(basedir, '.leapp', 'info'), 'w') as f:
            json.dump(data, f)
            return True
    return False


def get_repository_id(path):
    """
    Retrieves the repository name from the repository metadata from within the given path. (it can be anywhere within
    the repository it will use :py:func:`find_repository_dir` to find the repository base directory)
    :param path: Path within the leapp repository
    :return: ID of the repository
    :raises: KeyError if no name was found (e.g. not a valid repository path)
    """
    try:
        return get_repository_metadata(path)['id']
    except KeyError:
        if get_repository_metadata(path):
            return _create_and_set_repository_id(path)
        raise


def get_user_config_path():
    """
    Returns the path to the user configuration directory and creates it if it does not exist already.

    :return: Path to the configuration directory of leapp.
    """
    leapp_conf = os.path.join(os.path.expanduser('~'), '.config', 'leapp')
    try:
        os.makedirs(leapp_conf)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return leapp_conf


def get_user_config_repos():
    """
    Returns the path to the user config file for repositories.

    :return: Path to the repos.json configuration file.
    """
    return os.path.join(get_user_config_path(), 'repos.json')


def get_user_config_repo_data():
    """
    Returns the user config repository data.

    :return: Data for user configurations.
    """
    repos = get_user_config_repos()
    if not os.path.isfile(repos):
        return {}
    with open(repos) as f:
        return json.load(f)


def find_repos(path):
    """
    Finds repositories within the given path.

    :param path: Path to search for repositories.
    :return: List of strings with found repository paths.
    """
    try:
        with open(os.devnull, 'w') as devnull:
            data = subprocess.check_output(
                ['/usr/bin/find', '-L', path, '-name', '.leapp'], stderr=devnull).decode('utf-8').split('\n')
            return [os.path.abspath(os.path.dirname(rpath)) for rpath in data if rpath.strip()]
    except subprocess.CalledProcessError:
        return ()


def get_global_repositories_data():
    """
    Returns the data of all system wide available repositories.

    :return: Repository information
    """
    enabled = set([os.path.realpath(path) for path in find_repos('/etc/leapp/repos.d') if path.strip()])
    all_repos = set([os.path.realpath(path) for path in find_repos('/usr/share/leapp-repository') if path.strip()])
    repo_data = {}
    for repo in all_repos:
        repo_id = get_repository_metadata(repo).get('uuid', None)
        if not repo_id:
            continue
        repo_data[repo_id] = {
            'id': repo_id,
            'path': repo,
            'name': get_repository_name(repo),
            'enabled': repo in enabled
        }
    return repo_data
