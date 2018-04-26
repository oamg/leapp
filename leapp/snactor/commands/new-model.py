import os

import sys

from leapp.utils.project import requires_project, make_class_name, find_project_basedir
from leapp.utils.clicmd import command_arg, command
from leapp.exceptions import UsageError


_LONG_DESCRIPTION = '''
Creates a new Model with all necessary boilerplate code in the current
repository.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs 
'''


@command('new-model', help='Creates a new model', description=_LONG_DESCRIPTION)
@command_arg('model-name')
@requires_project
def cli(args):
    model_name = args.model_name
    basedir = find_project_basedir('.')

    basedir = os.path.join(basedir, 'models')
    if not os.path.isdir(basedir):
        os.mkdir(basedir)

    model_path = os.path.join(basedir, model_name.lower() + '.py')
    if os.path.exists(model_path):
        raise UsageError("File already exists: {}".format(model_path))

    with open(model_path, 'w') as f:
        f.write('''from leapp.models import Model, fields


class {model_name}(Model):
    topic = None #  TODO: import appropriate topic and set it here
'''.format(model_name=make_class_name(model_name)))

    sys.stdout.write("New model {} has been created in {}\n".format(make_class_name(model_name),
                                                                    os.path.realpath(model_path)))
