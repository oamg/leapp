import json as json_mod
import os
import sys

from leapp.actors import get_actor_metadata
from leapp.topics import get_topics
from leapp.models import get_models
from leapp.repository.scan import scan_repo
from leapp.tags import get_tags
from leapp.snactor.utils import find_project_basedir, get_project_name, requires_project
from leapp.utils.clicmd import command, command_opt


def _is_local(base_dir, cls):
    return os.path.realpath(sys.modules[cls.__module__].__file__).startswith(base_dir)


def _print_group(name, items, name_resolver=lambda item: item.__name__,
                 path_resolver=lambda x, y: _get_class_file(x, y)):
    sys.stdout.write('{group}:\n'.format(group=name))
    for item in sorted(items, key=lambda x: name_resolver(x)):
        sys.stdout.write('   - {name:<35} {path}\n'.format(name=name_resolver(item), path=path_resolver(item, False)))
    sys.stdout.write('\n')


def _get_actor_path(actor, project_relative=True):
    path = actor.directory
    return os.path.relpath(path, find_project_basedir('.') if project_relative else os.getcwd())


def _get_class_file(cls, project_relative=True):
    path = os.path.abspath(sys.modules[cls.__module__].__file__.replace('.pyc', '.py'))
    return os.path.relpath(path, find_project_basedir('.') if project_relative else os.getcwd())


def _get_actor_details(actor):
    meta = get_actor_metadata(actor)
    meta['produces'] = tuple(model.__name__ for model in meta['produces'])
    meta['consumes'] = tuple(model.__name__ for model in meta['consumes'])
    meta['tags'] = tuple(tag.name for tag in meta['tags'])
    meta['path'] = _get_class_file(actor)
    return meta


def _get_tag_details(tag):
    return {'actors': [actor.__name__ for actor in tag.actors],
            'name': tag.name}


def _get_topic_details(topic):
    return {'name': topic().name,
            'path': _get_class_file(topic)}


def _get_model_details(model):
    return {'path': _get_class_file(model)}


@command('discover')
@command_opt('json', is_flag=True)
@requires_project
def cli(args):
    base_dir = find_project_basedir('.')
    repository = scan_repo(base_dir)
    repository.load()

    actors = [actor for actor in repository.actors]
    models = [model for model in get_models() if _is_local(base_dir, model)]
    topics = [topic for topic in get_topics() if _is_local(base_dir, topic)]
    tags = [tag for tag in get_tags() if _is_local(base_dir, tag)]
    if not args.json:
        _print_group('Models', models)
        _print_group('Topics', topics)
        _print_group('Actors', actors, name_resolver=lambda x: x.class_name, path_resolver=_get_actor_path)
        _print_group('Tags', tags)
    else:
        output = {
            'project': get_project_name(base_dir),
            'base_dir': base_dir,
            'topics': {topic.__name__: _get_topic_details(topic) for topic in topics},
            'models': {model.__name__: _get_model_details(model) for model in models},
            'actors': {actor.class_name: _get_actor_details(actor) for actor in actors},
            'tags': {tag.name: _get_tag_details(tag) for tag in tags}
        }
        json_mod.dump(output, sys.stdout, indent=2)
