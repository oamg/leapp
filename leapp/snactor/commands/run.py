import datetime
import json
import os
import sys
from importlib import import_module

from leapp.exceptions import CommandError, LeappError
from leapp.logger import configure_logger
from leapp.messaging.inprocess import InProcessMessaging
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.context import with_snactor_context
from leapp.utils.clicmd import command, command_arg, command_opt
from leapp.utils.output import beautify_actor_exception, report_deprecations, report_errors
from leapp.utils.repository import find_repository_basedir, requires_repository

_LONG_DESCRIPTION = '''
Runs the given actor as specified as `actor_name` in a testing environment.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('run', help='Execute the given actor', description=_LONG_DESCRIPTION)
@command_arg('actor-name')
@command_opt('--actor-config', help='Name of the workflow config model to use')
@command_opt('--save-output', is_flag=True, help='Save the produced messages by this actor.')
@command_opt('--print-output', is_flag=True, help='Print the produced messages by this actor.')
@requires_repository
@with_snactor_context
def cli(args):
    start = datetime.datetime.utcnow()
    log = configure_logger()
    basedir = find_repository_basedir('.')
    repository = find_and_scan_repositories(basedir, include_locals=True)
    try:
        repository.load()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.stderr.write('\n')
        sys.exit(1)
    actor_logger = log.getChild('actors')
    actor = repository.lookup_actor(args.actor_name)
    if not actor:
        raise CommandError('Actor "{}" not found!'.format(args.actor_name))
    config_model = getattr(import_module('leapp.models'), args.actor_config) if args.actor_config else None
    messaging = InProcessMessaging(stored=args.save_output, config_model=config_model)
    messaging.load(actor.consumes)

    failure = False
    with beautify_actor_exception():
        try:
            actor(messaging=messaging, logger=actor_logger, config_model=config_model).run()
        except BaseException:
            failure = True
            raise

    report_errors(messaging.errors())
    report_deprecations(os.getenv('LEAPP_EXECUTION_ID'), start=start)

    if failure or messaging.errors():
        sys.exit(1)

    if args.print_output:
        json.dump(messaging.messages(), sys.stdout, indent=2)
        sys.stdout.write('\n')
