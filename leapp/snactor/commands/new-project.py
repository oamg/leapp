import json
import os
import sys

from leapp.utils.clicmd import command_arg, command

_PROJECT_CONFIG = '''
[repositories]
repo_path=${project:root_dir}

[database]
path=${project:state_dir}/leapp.db
'''


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
                'name': name
            }, f)
        with open(os.path.join(project_dir, 'leapp.conf'), 'w') as f:
            f.write(_PROJECT_CONFIG)

        sys.stdout.write("New project {} has been created in {}\n".format(name, os.path.realpath(name)))
