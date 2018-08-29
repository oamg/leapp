import os

import sys

from leapp.utils.clicmd import command_arg, command
from leapp.exceptions import CommandError
from leapp.utils.repository import requires_repository, make_class_name, make_name, find_repository_basedir

_LONG_DESCRIPTION = '''
Creates a new Tag in the current repository.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('new-tag', help='Create a new tag', description=_LONG_DESCRIPTION)
@command_arg('tag-name')
@requires_repository
def cli(args):
    basedir = os.path.join(find_repository_basedir('.'), 'tags')
    if not os.path.isdir(basedir):
        os.mkdir(basedir)

    tag_path = os.path.join(basedir, args.tag_name.lower() + '.py')
    if os.path.exists(tag_path):
        raise CommandError("File already exists: {}".format(tag_path))

    tag_class_name = make_class_name(tag_name)
    if not tag_class_name.endswith('Tag'):
        tag_class_name += 'Tag'
    with open(tag_path, 'w') as f:
        f.write('''from leapp.tags import Tag


class {tag_name}(Tag):
    name = '{tag}'
'''.format(tag_name=tag_class_name, tag=make_name(args.tag_name)))

    sys.stdout.write("New tag {} has been created in {}\n".format(tag_class_name, os.path.realpath(tag_path)))
