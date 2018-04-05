import json
import os
import sys

from leapp.utils.clicmd import command_arg, command


@command('new-project', help='Creates a new project')
@command_arg('name')
def cli(args):
    name = args.name
    basedir = os.path.join('.', name)
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
        project_dir = os.path.join(basedir, '.leapp')
        os.mkdir(project_dir)
        with open(os.path.join(project_dir, 'info'), 'w') as f:
            json.dump({
                'name': name,
                'messages': {}
            }, f)
        sys.stdout.write("New project {} has been created in {}\n".format(name, os.path.realpath(name)))
