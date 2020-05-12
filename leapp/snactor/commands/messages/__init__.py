import json
import os
import sys
from importlib import import_module

from leapp.exceptions import CommandError, LeappError, ModelDefinitionError
from leapp.logger import configure_logger
from leapp.messaging.inprocess import InProcessMessaging
from leapp.models.fields import ModelViolationError
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.context import with_snactor_context
from leapp.utils.audit import get_config, get_connection
from leapp.utils.clicmd import command, command_arg, command_opt
from leapp.utils.repository import find_repository_basedir, requires_repository

_MAIN_LONG_DESCRIPTION = '''
This group of commands are around managing messages stored in the
current repository database.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('messages', help='Messaging related commands', description=_MAIN_LONG_DESCRIPTION)
def messages(args):  # noqa; pylint: disable=unused-argument
    pass


_CLEAR_LONG_DESCRIPTION = '''
With this command messages in the current repository scope can be wiped.
This gives the developer control over the input data available to actors
run and developed in this repository.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


_ADD_LONG_DESCRIPTION = '''
With this command messages in the current repository scope can be added.
This gives the developer control over the input data available to actors
run and developed in this repository.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@messages.command('clear', help='Deletes all messages from the current repository scope',
                  description=_ADD_LONG_DESCRIPTION)
@requires_repository
@with_snactor_context
def clear(args):  # noqa; pylint: disable=unused-argument
    print("Deleting all messages with context = {} in database {}".format(
        os.environ["LEAPP_EXECUTION_ID"],
        get_config().get("database", "path")
    ))
    with get_connection(None) as con:
        con.execute("DELETE FROM message WHERE context = ?", (os.environ["LEAPP_EXECUTION_ID"],))


class Injector(object):
    name = 'injector'


@messages.command('add', help='Adds a message to the current repository scope',
                  description=_CLEAR_LONG_DESCRIPTION)
@command_opt('model', short_name='m', help='Model to add')
@command_arg('data', help='Data to add in JSON format')
@requires_repository
@with_snactor_context
def add(args):  # noqa; pylint: disable=unused-argument
    basedir = find_repository_basedir('.')
    repository = find_and_scan_repositories(basedir, include_locals=True)
    try:
        repository.load()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.stderr.write('\n')
        sys.exit(1)
    try:
        model = getattr(import_module('leapp.models'), args.model, None)
        InProcessMessaging().produce(model.create(json.loads(args.data)), Injector())
    except ModelDefinitionError:
        raise CommandError('No such model: {}'.format(args.model))
    except ModelViolationError as e:
        raise CommandError('Invalid data format for model: {}\n    => {}'.format(args.model, e.message))
