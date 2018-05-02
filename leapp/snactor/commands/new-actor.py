import os
import sys

from leapp.utils.project import requires_project, make_class_name, make_name, find_project_basedir
from leapp.utils.clicmd import command, command_arg
from leapp.exceptions import UsageError


_LONG_DESCRIPTION = '''
Creates a new Actor with all necessary boilerplate code in the current
repository.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('new-actor', help='Creates a new actor', description=_LONG_DESCRIPTION)
@command_arg('actor-name')
@requires_project
def cli(args):
    actor_name = args.actor_name
    basedir = find_project_basedir('.')

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
        raise UsageError("File already exists: {}".format(actor_path))

    with open(actor_path, 'w') as f:
        f.write('''from leapp.actors import Actor


class {actor_class}(Actor):
    name = '{actor_name}'
    description = 'No description has been provided for the {actor_name} actor.'
    consumes = ()
    produces = ()
    tags = ()

    def process(self):
        pass
'''.format(actor_class=make_class_name(actor_name), actor_name=make_name(actor_name)))

    sys.stdout.write("New actor {} has been created at {}\n".format(make_class_name(actor_name),
                                                                    os.path.realpath(actor_path)))
