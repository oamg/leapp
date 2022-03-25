import os
import sys

from leapp.utils.repository import requires_repository, make_class_name, make_name, find_repository_basedir
from leapp.utils.clicmd import command, command_arg, command_opt
from leapp.exceptions import CommandError


_LONG_DESCRIPTION = '''
Creates a new Actor with all necessary boilerplate code in the current
repository.

The options --tags, --consumes, and --produces can be used multiple times, for multiple values.
Example:
  $ snactor new-actor ExampleActor --tag SomeWorkflowTag --tag AnotherTag --produces ImportantModel


For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


def quoted(x):
    return "'" + x + "'"


def as_quoted_tuple(values):
    if values:
        suffix = ''
        if len(values) == 1:
            suffix = ','
        return ', '.join(values) + suffix
    return ''


@command('new-actor', help='Creates a new actor', description=_LONG_DESCRIPTION)
@command_arg('actor-name')
@command_opt('--tag', action='append', metavar='TagClassName', help='Existing Tag to add to the tags field')
@command_opt('--consumes', action='append', metavar='ModelClassName',
             help='Existing Model to add to the consumes field')
@command_opt('--produces', action='append', metavar='ModelClassName',
             help='Existing Model to add to the produces field')
@requires_repository
def cli(args):
    actor_name = args.actor_name
    basedir = find_repository_basedir('.')

    tag_imports = ''
    model_imports = ''
    if args.tag:
        tag_imports = '\nfrom leapp.tags import {}'.format(', '.join(tuple(x.split('.')[0] for x in args.tag)))
    if args.consumes or args.produces:
        models = set((args.produces or []) + (args.consumes or []))
        model_imports = '\nfrom leapp.models import {}'.format(', '.join(models))

    tags_content = '({})'.format(as_quoted_tuple(args.tag))
    consumes_content = '({})'.format(as_quoted_tuple(args.consumes))
    produces_content = '({})'.format(as_quoted_tuple(args.produces))

    actors_dir = os.path.join(basedir, 'actors')
    if not os.path.isdir(actors_dir):
        os.mkdir(actors_dir)

    actor_dir = os.path.join(actors_dir, actor_name.lower())
    if not os.path.isdir(actor_dir):
        os.mkdir(actor_dir)

    actor_test_dir = os.path.join(actor_dir, 'tests')
    if not os.path.isdir(actor_test_dir):
        os.mkdir(actor_test_dir)

    actor_path = os.path.join(actor_dir, 'actor.py')
    if os.path.exists(actor_path):
        raise CommandError("File already exists: {}".format(actor_path))

    with open(actor_path, 'w') as f:
        f.write('''from leapp.actors import Actor{model_imports}{tag_imports}


class {actor_class}(Actor):
    """
    No documentation has been provided for the {actor_name} actor.
    """

    name = '{actor_name}'
    consumes = {consumes_content}
    produces = {produces_content}
    tags = {tags_content}

    def process(self):
        pass
'''.format(actor_class=make_class_name(actor_name), actor_name=make_name(actor_name), tags_content=tags_content,
           produces_content=produces_content, consumes_content=consumes_content,
           model_imports=model_imports, tag_imports=tag_imports))

    sys.stdout.write("New actor {} has been created at {}\n".format(make_class_name(actor_name),
                                                                    os.path.realpath(actor_path)))
    return os.path.dirname(os.path.realpath(actor_path))
