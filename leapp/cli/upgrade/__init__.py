from __future__ import print_function
import itertools
import json
import os
import sys
import uuid

from leapp.config import get_config
from leapp.exceptions import CommandError, LeappError
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.utils.audit import Execution, get_connection, get_checkpoints
from leapp.utils.clicmd import command, command_opt
from leapp.utils.output import report_errors, beautify_actor_exception


def load_repositories_from(name, repo_path, manager=None):
    if get_config().has_option('repositories', name):
        repo_path = get_config().get('repositories', name)
    return find_and_scan_repositories(repo_path, manager=manager)


def load_repositories():
    manager = load_repositories_from('repo_path', '/etc/leapp/repo.d/', manager=None)
    manager.load()
    return manager


def fetch_last_upgrade_context():
    """
    :return: Context of the last execution
    """
    with get_connection(None) as db:
        cursor = db.execute(
            "SELECT context, stamp, configuration FROM execution WHERE kind = 'upgrade' ORDER BY stamp DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row[0], json.loads(row[2])
    return None, {}


def fetch_all_upgrade_contexts():
    """
    :return: All upgrade execution contexts
    """
    with get_connection(None) as db:
        cursor = db.execute(
            "SELECT context, stamp, configuration FROM execution WHERE kind = 'upgrade' ORDER BY stamp DESC")
        row = cursor.fetchall()
        if row:
            return row
    return None


def get_last_phase(context):
    checkpoints = get_checkpoints(context=context)
    if checkpoints:
        return checkpoints[-1]['phase']


@command('upgrade', help='Upgrades the current system to the next available major version.')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
@command_opt('reboot', is_flag=True, help='Automatically performs reboot when requested.')
@command_opt('--whitelist-experimental', action='append', metavar='ActorName',
             help='Enables experimental actors')
def upgrade(args):
    if os.getuid():
        raise CommandError('This command has to be run under the root user.')

    if args.whitelist_experimental:
        args.whitelist_experimental = list(itertools.chain(*[i.split(',') for i in args.whitelist_experimental]))
    skip_phases_until = None
    context = str(uuid.uuid4())
    configuration = {
        'debug': os.getenv('LEAPP_DEBUG', '0'),
        'verbose': os.getenv('LEAPP_VERBOSE', '0'),
        'whitelist_experimental': args.whitelist_experimental or ()
    }
    if args.resume:
        context, configuration = fetch_last_upgrade_context()
        if not context:
            raise CommandError('No previous upgrade run to continue, remove `--resume` from leapp invocation to'
                               'start a new upgrade flow')
        os.environ['LEAPP_DEBUG'] = '1' if os.getenv('LEAPP_DEBUG', configuration.get('debug', '0')) == '1' else '0'

        if os.environ['LEAPP_DEBUG'] == '1' or os.getenv('LEAPP_VERBOSE', configuration.get('verbose', '0')) == '1':
            os.environ['LEAPP_VERBOSE'] = '1'
        else:
            os.environ['LEAPP_VERBOSE'] = '0'

        skip_phases_until = get_last_phase(context)
    else:
        e = Execution(context=context, kind='upgrade', configuration=configuration)
        e.store()
    os.environ['LEAPP_EXECUTION_ID'] = context

    logger = configure_logger()

    if args.resume:
        logger.info("Resuming execution after phase: %s", skip_phases_until)
    try:
        repositories = load_repositories()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.stderr.write('\n')
        raise CommandError(exc.message)
    workflow = repositories.lookup_workflow('IPUWorkflow')(auto_reboot=args.reboot)
    for actor_name in configuration.get('whitelist_experimental', ()):
        actor = repositories.lookup_actor(actor_name)
        if actor:
            workflow.whitelist_experimental_actor(actor)
        else:
            msg = 'No such Actor: {}'.format(actor_name)
            logger.error(msg)
            raise CommandError(msg)
    with beautify_actor_exception():
        workflow.run(context=context, skip_phases_until=skip_phases_until)

    report_errors(workflow.errors)


@command('list-runs', help='List previous Leapp upgrade executions')
def list_runs(args):
    contexts = fetch_all_upgrade_contexts()
    if contexts:
        for context in contexts:
            print('Context ID: {} - time: {} - details: {}'.format(context[0], context[1], json.loads(context[2])),
                  file=sys.stdout)
    else:
        raise CommandError('No previous run found!')
