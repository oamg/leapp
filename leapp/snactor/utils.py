import functools
import json
import os
import pkgutil
import re

from leapp.utils.clicmd import UsageError


def requires_project(f):
    @functools.wraps(f)
    def checker(*args, **kwargs):
        if not find_project_basedir('.'):
            raise UsageError('This command must be executed from the project directory')
        return f(*args, **kwargs)
    return checker


def load_modules(pkg_path, use_repo=None):
    modules = []
    for importer, name, is_pkg in pkgutil.iter_modules([pkg_path]):
        if is_pkg:
            continue
        if use_repo:
            for actor in use_repo.actors:
                actor_dir = os.path.dirname(actor.directory)
                if importer.path.endswith(actor_dir):
                    with actor.injected_context():
                        modules.append(importer.find_module(name).load_module(name))
                    break
        else:
            modules.append(importer.find_module(name).load_module(name))
    return modules


def load_modules_from(path, use_repo=None):
    if os.path.exists(path):
        if load_modules(path, use_repo=use_repo):
            return
        for root, _, _ in os.walk(path):
            load_modules(root, use_repo=use_repo)


def load_all_from(basedir, use_repo=None):
    for directory in ('topics', 'models', 'tags', 'actors', 'workflows'):  # Order is NOT arbitrary - keep the order
        modules_dir = os.path.join(basedir, directory)
        load_modules_from(modules_dir, use_repo=use_repo if directory == 'actors' else None)


def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name.replace('-', '_'))
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def make_class_name(name):
    return ''.join(map(lambda x: x.capitalize(), to_snake_case(name).split('_')))


def make_name(name):
    return to_snake_case(name).lower()


def find_project_basedir(path):
    path = os.path.realpath(path)
    while True:
        if os.path.isdir(os.path.join(path, '.leapp')):
            return path
        path, current = os.path.split(path)
        if not current:
            return None


def get_project_metadata(path):
    basedir = find_project_basedir(path)
    if basedir:
        with open(os.path.join(basedir, '.leapp', 'info'), 'r') as f:
            return json.load(f)
    return {}


def get_project_name(path):
    return get_project_metadata(path)['name']
