import json as json_mod
import os
import sys

from leapp.exceptions import LeappError
from leapp.topics import get_topics
from leapp.models import get_models
from leapp.repository.scan import scan_repo
from leapp.tags import get_tags
from leapp.utils.project import requires_project, find_project_basedir, get_project_name
from leapp.utils.clicmd import command, command_opt
from leapp.workflows import get_workflows


def _is_local(base_dir, cls):
    return os.path.realpath(sys.modules[cls.__module__].__file__).startswith(base_dir)


def _print_group(name, items, name_resolver=lambda item: item.__name__,
                 path_resolver=lambda x, y: _get_class_file(x, y)):
    sys.stdout.write('{group}({count}):\n'.format(group=name, count=len(items)))
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
    meta = actor.discover()
    meta['produces'] = tuple(model.__name__ for model in meta['produces'])
    meta['consumes'] = tuple(model.__name__ for model in meta['consumes'])
    meta['tags'] = tuple(tag.name for tag in meta['tags'])
    meta['path'] = _get_class_file(actor)
    return meta


def _get_workflow_details(workflow):
    return {'name': workflow.name, 'description': workflow.description, 'short_name': workflow.short_name}


def _get_tag_details(tag):
    return {'actors': [actor.class_name for actor in tag.actors],
            'name': tag.name}


def _get_topic_details(topic):
    return {'name': topic().name,
            'path': _get_class_file(topic)}


def _get_model_details(model):
    return {'path': _get_class_file(model)}


_LONG_DESCRIPTION = '''
Discovers and displays supported entities from the current repository.

Support entities:
- Actors
- Models
- Tags
- Topics
- Workflows


For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('discover', help="Discovers all available entities in the current project repository",
         description=_LONG_DESCRIPTION)
@command_opt('json', is_flag=True, help='Output in json format instead of human readable form')
@requires_project
def cli(args):
    base_dir = find_project_basedir('.')
    repository = scan_repo(base_dir)
    try:
        repository.load()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.exit(1)

    actors = [actor for actor in repository.actors]
    models = [model for model in get_models() if _is_local(base_dir, model)]
    topics = [topic for topic in get_topics() if _is_local(base_dir, topic)]
    tags = [tag for tag in get_tags() if _is_local(base_dir, tag)]
    workflows = [workflow for workflow in get_workflows() if _is_local(base_dir, workflow)]
    if not args.json:
        sys.stdout.write(
            'Project:\n  Name: {project}\n  Path: {base_dir}\n\n'.format(project=get_project_name(base_dir),
                                                                         base_dir=base_dir))
        _print_group('Actors', actors, name_resolver=lambda x: x.class_name, path_resolver=_get_actor_path)
        _print_group('Models', models)
        _print_group('Tags', tags)
        _print_group('Topics', topics)
        _print_group('Workflows', workflows)
    else:
        output = {
            'project': get_project_name(base_dir),
            'base_dir': base_dir,
            'topics': dict((topic.__name__, _get_topic_details(topic)) for topic in topics),
            'models': dict((model.__name__, _get_model_details(model)) for model in models),
            'actors': dict((actor.class_name, _get_actor_details(actor)) for actor in actors),
            'tags': dict((tag.name, _get_tag_details(tag)) for tag in tags),
            'workflows': dict((workflow.__name__, _get_workflow_details(workflow)) for workflow in workflows)
        }
        json_mod.dump(output, sys.stdout, indent=2)
