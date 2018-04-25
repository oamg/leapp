import json
import os
import sys
import uuid

from leapp.utils.audit import Execution, get_connection
from leapp.utils.clicmd import command, command_opt, command_arg
from leapp.logger import configure_logger
from leapp.utils.project import requires_project, find_project_basedir
from leapp.messaging.inprocess import InProcessMessaging
from leapp.repository.scan import scan_repo


def _set_execution_context():
    cursor = get_connection(None).execute("""
      SELECT context, stamp FROM execution WHERE kind = 'snactor-run' ORDER BY stamp DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        context = row[0]
    else:
        context = str(uuid.uuid4())
        Execution(context=str(uuid.uuid4()), kind='snactor-run', configuration='').store()
    os.environ["LEAPP_EXECUTION_ID"] = context


@command('run', help='Execute the given actor')
@command_arg('actor-name')
@command_opt('--save-output', is_flag=True)
@command_opt('--print-output', is_flag=True)
@requires_project
def cli(args):
    _set_execution_context()
    log = configure_logger()
    basedir = find_project_basedir('.')
    repository = scan_repo(basedir)
    repository.load()
    actor_logger = log.getChild('actors')
    actor = repository.lookup_actor(args.actor_name)
    messaging = InProcessMessaging(stored=False)
    messaging.load(actor.consumes)

    actor(messaging=messaging, logger=actor_logger).run()
    if args.save_output:
        messaging.store()
    if args.print_output:
        json.dump(messaging.get_new(), sys.stdout, indent=2)
