import os

import sys

from leapp.utils.repository import make_class_name, make_name, find_repository_basedir
from leapp.utils.clicmd import command_arg, command
from leapp.exceptions import UsageError

_LONG_DESCRIPTION = '''
Creates a new Topic in the current repository.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('new-topic', help='Creates a new topic')
@command_arg('topic-name')
def cli(args):
    topic_name = args.topic_name
    basedir = find_repository_basedir('.')

    basedir = os.path.join(basedir, 'topics')
    if not os.path.isdir(basedir):
        os.mkdir(basedir)

    topic_path = os.path.join(basedir, topic_name.lower() + '.py')
    if os.path.exists(topic_path):
        raise UsageError("File already exists: {}".format(topic_path))

    topic_path = os.path.join(basedir, topic_name.lower() + '.py')
    with open(topic_path, 'w') as f:
        f.write('''from leapp.topics import Topic


class {topic_name}Topic(Topic):
    name = '{topic}'
'''.format(topic_name=make_class_name(topic_name), topic=make_name(topic_name)))

    sys.stdout.write("New topic {} has been created in {}\n".format(make_class_name(topic_name),
                                                                    os.path.realpath(topic_path)))
