from leapp.utils.clicmd import command, command_opt
from leapp.repository.scan import find_and_scan_repositories
from leapp.config import get_config
from leapp.logger import configure_logger


def load_repositories_from(name, repo_path, manager=None):
    if get_config().has_option('repositories', name):
        repo_path = get_config().get('repositories', name)
    return find_and_scan_repositories(repo_path, manager=manager)


def load_repositories():
    load_repositories_from('custom_repo_path', '/etc/leapp/repos.d/', manager=None)
    manager.load()
    return manager


@command('upgrade', help='')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
def upgrade(args):
    configure_logger()
    repositories = load_repositories()
    workflow = repositories.lookup_workflow('IPUWorkflow')
    workflow.run()
