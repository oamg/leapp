import os

import sys

from leapp.utils.clicmd import command_arg, command, UsageError
from leapp.snactor.utils import find_project_basedir, make_name, make_class_name, requires_project


@command('new-tag', help='Create a new tag')
@command_arg('tag-name')
@requires_project
def cli(args):
    basedir = find_project_basedir('.')
    if not basedir:
        raise UsageError('This command must be executed from the project directory')

    basedir = os.path.join(basedir, 'tags')
    if not os.path.isdir(basedir):
        os.mkdir(basedir)

    tag_path = os.path.join(basedir, args.tag_name.lower() + '.py')
    if os.path.exists(tag_path):
        raise UsageError("File already exists: {}".format(tag_path))

    with open(tag_path, 'w') as f:
        f.write('''from leapp.tags import Tag


class {tag_name}Tag(Tag):
    name = '{tag}'
'''.format(tag_name=make_class_name(args.tag_name), tag=make_name(args.tag_name)))

    sys.stdout.write("New tag {} has been created in {}\n".format(make_class_name(args.tag_name),
                                                                  os.path.realpath(tag_path)))
