from __future__ import print_function
import json
import os
import subprocess
import sys

from leapp.utils.clicmd import command, command_opt, command_arg
from leapp.utils.repository import requires_repository, find_repository_basedir, get_repository_name, \
    get_repository_id, add_repository_link, get_user_config_repos, get_user_config_repo_data, \
    get_global_repositories_data
from leapp.exceptions import CommandError, UsageError

_MAIN_LONG_DESCRIPTION = '''
This group of commands are around managing repositories.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('repo', help='Repository related commands', description=_MAIN_LONG_DESCRIPTION)
def repo(args):  # noqa; pylint: disable=unused-argument
    pass


_HEALTH_CHECK_LONG_DESCRIPTION = '''
Health check is used to remove stale repository entries from the user local repository registration.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@repo.command('health-check', help='Checks registered repositories and removes missing entries',
              description=_HEALTH_CHECK_LONG_DESCRIPTION)
def health_check(args):  # noqa; pylint: disable=unused-argument
    to_remove = []
    data = get_user_config_repo_data()
    if not data:
        return
    for uuid, path in data.get('repos', {}).items():
        if not os.path.isdir(path):
            print('Removing repository {uuid} => {path}'.format(uuid=uuid, path=path))
            to_remove.append(uuid)
    for uuid in to_remove:
        data.get('repos', {}).pop(uuid, None)
    with open(get_user_config_repos(), 'w') as f:
        json.dump(data, f)


_LIST_LONG_DESCRIPTION = '''
Lists repositories on the system. By default it will list all registered user repositories.

It also can list global repositories on the system which usually reside in /usr/share/leapp-repository/
by using the --global commandline flag.

When using the --all commandline flag, all repositories user and globally are listed.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@repo.command('list', help='Lists repositories', description=_LIST_LONG_DESCRIPTION)
@command_opt('global', is_flag=True, help='List globally available repositories only.')
@command_opt('all', is_flag=True, help='List all available user and global repositories.')
def list_repos(args):
    global_repos = {}
    if getattr(args, 'global', None) or args.all:
        global_repos = get_global_repositories_data()

    for entry in global_repos.values():
        print('{name:<35} [{uuid}] => {path}'.format(name=entry['name'], path=entry['path'], uuid=entry['id']))

    if not getattr(args, 'global', None):
        user_repos = get_user_config_repo_data()
        for path in user_repos.get('repos', {}).values():
            if os.path.isdir(path):
                name = get_repository_name(path)
                uuid = get_repository_id(path)
                print('{name:<35} [{uuid}] => {path}'.format(name=name, path=path, uuid=uuid))


def register_path(path):
    """
    Calling this function will register a path to be a well
    :param path: Path to the repository repository
    :return:
    """
    path = os.path.abspath(os.path.realpath(path))
    data = {}
    repos = get_user_config_repos()
    if os.path.isfile(repos):
        with open(repos) as f:
            data = json.load(f)
    data.setdefault('repos', {}).update({get_repository_id(path): path})
    with open(repos, 'w') as f:
        json.dump(data, f)


_REGISTER_LONG_DESCRIPTION = '''
Registers the current user repository in the users repository registry.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@repo.command('register', help='Registers the current repository in the user repository registry.',
              description=_REGISTER_LONG_DESCRIPTION)
@requires_repository
def register_repo(args):  # noqa; pylint: disable=unused-argument
    base_dir = find_repository_basedir('.')
    if base_dir:
        register_path(base_dir)
        print('Repository successfully registered')


_LINK_LONG_DESCRIPTION = '''
Links a given repository to the current repository.

Linking a repository is needed, when the current repository requires things like
Tags, Models, Topics, Workflows etc from another repository and needs to be executable
with `snactor`. Snactor does not know otherwise that it will need to load the content
from another repository. Linking the repositories will make snactor load the items
from the linked repositories.

Repositories can be linked by path, name and repository id.

When using the repository name, beware that the first matching name will be linked.
Therefore it's recommended to rather link repositories by path or repository id.

Usage:
    $ snactor repo link --path ../../other-repository

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@repo.command('link', help='Links a given repository to the current one', description=_LINK_LONG_DESCRIPTION)
@command_opt('path', help='Path to the repository to link')
@command_opt('name', help='Name of the repository to link')
@command_opt('uuid', help='UUID of the repository to link', )
@requires_repository
def link_repo(args):
    if not any((args.path, args.name, args.uuid)):
        raise UsageError('Please specify either --path, --name or --uuid to link another repository.')
    data = get_user_config_repo_data()
    path = args.path
    if not path:
        if args.uuid:
            path = data.get('repos', {}).get(args.uuid, None)
        elif args.name:
            for repository_path in data.get('repos', {}).values():
                if os.path.isdir(repository_path):
                    if args.name == get_repository_name(repository_path):
                        path = repository_path
                        break
    if not path:
        raise UsageError('Please specify a valid repository name, uuid or path')

    if add_repository_link('.', get_repository_id(path)):
        print('Added link to repository {path} - {name}'.format(path=path, name=get_repository_name(path)))


_FIND_LONG_DESCRIPTION = '''
Searches for all repositories and registers them.

When not specifying --path - It will search from the current working directory for existing
leapp repositories and registers all found repositories with the users repository registration.

By using --skip-registration it can be used to just detect repositories without registering them.

If another path should be scanned than the current working directory pass the --path flag.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@repo.command('find', help='Find and registers all repositories')
@command_opt('skip-registration', is_flag=True, help='Do not register discovered repositories.')
@command_opt('path', help='Path to scan from - If not specified the current working directory is assumed')
def find_repositories(args):
    path = args.path or os.path.realpath('.')
    result = subprocess.check_output(['/usr/bin/find', '-L', path, '-name', '.leapp']).decode('utf-8')
    for repository in result.split('\n'):
        if repository.strip():
            repository = os.path.dirname(repository)
            if not args.skip_registration:
                print('Registering {path}'.format(path=repository))
                register_path(repository)
            else:
                print(repository)


_REPOSITORY_CONFIG = '''
[repositories]
repo_path=${repository:root_dir}

[database]
path=${repository:state_dir}/leapp.db
'''
_LONG_DESCRIPTION = '''
Creates a new local repository for writing Actors, Models, Tags,
Topics, and Workflows or adding shared files, tools or libraries.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@repo.command('new', help='Creates a new repository', description=_LONG_DESCRIPTION)
@command_arg('name')
def new_repository(args):
    name = args.name
    basedir = os.path.join('.', name)
    if os.path.isdir(basedir):
        raise CommandError("Directory already exists: {}".format(basedir))

    os.mkdir(basedir)
    repository_dir = os.path.join(basedir, '.leapp')
    os.mkdir(repository_dir)
    with open(os.path.join(repository_dir, 'info'), 'w') as f:
        json.dump({
            'name': name
        }, f)
    with open(os.path.join(repository_dir, 'leapp.conf'), 'w') as f:
        f.write(_REPOSITORY_CONFIG)

    register_path(basedir)
    sys.stdout.write("New repository {} has been created in {}\n".format(name, os.path.realpath(name)))
