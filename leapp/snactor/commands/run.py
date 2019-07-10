import json
import sys

from leapp.exceptions import LeappError, CommandError
from leapp.utils.clicmd import command, command_opt, command_arg
from leapp.utils.repository import requires_repository, find_repository_basedir
from leapp.logger import configure_logger
from leapp.messaging.inprocess import InProcessMessaging
from leapp.utils.output import report_errors, beautify_actor_exception
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.context import with_snactor_context


_LONG_DESCRIPTION = '''
Runs the given actor as specified as `actor_name` in a testing environment.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('run', help='Execute the given actor', description=_LONG_DESCRIPTION)
@command_arg('actor-name')
@command_opt('--save-output', is_flag=True)
@command_opt('--print-output', is_flag=True)
@requires_repository
@with_snactor_context
def cli(args):
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
    messaging = InProcessMessaging(stored=args.save_output)
    messaging.load(actor.consumes)

    failure = False
    with beautify_actor_exception():
        try:
            actor(messaging=messaging, logger=actor_logger).run()
        except BaseException:
            failure = True
            raise

    report_errors(messaging.errors())

    if failure or messaging.errors():
        sys.exit(1)

    if args.print_output:
        json.dump(messaging.messages(), sys.stdout, indent=2)
        sys.stdout.write('\n')
