import os
import uuid

from leapp.config import get_config
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.utils.audit import Execution, get_connection, get_checkpoints
from leapp.utils.clicmd import command, command_opt


def load_repositories_from(name, repo_path, manager=None):
    if get_config().has_option('repositories', name):
        repo_path = get_config().get('repositories', name)
    return find_and_scan_repositories(repo_path, manager=manager)


def load_repositories():
    manager = load_repositories_from('repo_path', '/etc/leapp/repos.d/', manager=None)
    manager.load()
    return manager


def fetch_last_upgrade_context():
    """
    :return: Context of the last execution
    """
    with get_connection(None) as db:
        cursor = db.execute("SELECT context, stamp FROM execution WHERE kind = 'upgrade' ORDER BY stamp DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row[0]
    return None


def get_last_phase(context):
    checkpoints = get_checkpoints(context=context)
    if checkpoints:
        return checkpoints[-1]['phase']


@command('upgrade', help='Upgrades the current system to the next available major version.')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
def upgrade(args):
    skip_phases_until = None
    context = str(uuid.uuid4())
    if args.resume:
        context = fetch_last_upgrade_context()
        skip_phases_until = get_last_phase(context)
    else:
        e = Execution(context=context, kind='upgrade', configuration={})
        e.store()
    os.environ['LEAPP_EXECUTION_ID'] = context

    logger = configure_logger()

    if args.resume:
        logger.info("Resuming execution after phase: %s", skip_phases_until)

    repositories = load_repositories()
    workflow = repositories.lookup_workflow('IPUWorkflow')
    workflow().run(context=context, skip_phases_until=skip_phases_until)
