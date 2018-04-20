import os
import uuid

from leapp.utils.clicmd import command, command_opt
from leapp.repository.scan import find_and_scan_repositories
from leapp.config import get_config
from leapp.logger import configure_logger
from leapp.utils.audit import Execution, get_connection


def load_repositories_from(name, repo_path, manager=None):
    if get_config().has_option('repositories', name):
        repo_path = get_config().get('repositories', name)
    return find_and_scan_repositories(repo_path, manager=manager)


def load_repositories():
    manager = load_repositories_from('repo_path', '/etc/leapp/repos.d/', manager=None)
    manager.load()
    return manager


def fetch_last_upgrade_context():
    db = get_connection(None)
    cursor = db.execute("SELECT context, stamp FROM execution WHERE kind = ? ORDER BY stamp DESC LIMIT 1")
    return cursor.fetchone()[0]


@command('upgrade', help='')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
def upgrade(args):
    context = str(uuid.uuid4())
    if args.resume:
        context = fetch_last_upgrade_context()
    else:
        e = Execution(context=context, kind='upgrade', configuration={})
        e.store()
    os.environ['LEAPP_EXECUTION_ID'] = context

    configure_logger()

    repositories = load_repositories()
    workflow = repositories.lookup_workflow('IPUWorkflow')
    workflow.run()
