import sys

from leapp.utils.clicmd import command_arg, command
from leapp.snactor.commands.repo import new_project

_LONG_DESCRIPTION = '''
DEPRECATED: Please use `snactor repo new` instead

Creates a new local repository for writing Actors, Models, Tags,
Topics, and Workflows or adding shared files, tools or libraries.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('new-project', help='[DEPRECATED] Creates a new project', description=_LONG_DESCRIPTION)
@command_arg('name')
def cli(args):
    sys.stderr.write('WARNING: This command has been deprecated. Please use `snactor repo new`\n')
    new_project(args)
