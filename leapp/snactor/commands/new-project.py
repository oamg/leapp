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

_LONG_DESCRIPTION = '''
Creates a new local repository for writing Actors, Models, Tags, 
Topics, and Workflows or adding shared files, tools or libraries.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs 
'''


@command('new-project', help='Creates a new project', description=_LONG_DESCRIPTION)
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
