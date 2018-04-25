import json
import sys

from leapp.utils.clicmd import command, command_opt, command_arg
from leapp.utils.project import requires_project, find_project_basedir
from leapp.logger import configure_logger
from leapp.messaging.inprocess import InProcessMessaging
from leapp.utils.output import report_errors
from leapp.repository.scan import scan_repo
from leapp.snactor.context import with_snactor_context


@command('run', help='Execute the given actor')
@command_arg('actor-name')
@command_opt('--save-output', is_flag=True)
@command_opt('--print-output', is_flag=True)
@requires_project
@with_snactor_context
def cli(args):
    log = configure_logger()
    basedir = find_project_basedir('.')
    repository = scan_repo(basedir)
    repository.load()
    actor_logger = log.getChild('actors')
    actor = repository.lookup_actor(args.actor_name)
    messaging = InProcessMessaging(stored=args.save_output)
    messaging.load(actor.consumes)

    actor(messaging=messaging, logger=actor_logger).run()

    report_errors(messaging.errors())

    if args.print_output:
        json.dump(messaging.messages(), sys.stdout, indent=2)

