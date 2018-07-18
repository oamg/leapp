import os

from leapp.repository import Repository, DefinitionKind
from leapp.repository.manager import RepositoryManager
from leapp.repository.actor_definition import ActorDefinition
from leapp.exceptions import RepositoryConfigurationError
from leapp.utils.project import get_global_repositories_data, get_user_config_repo_data, find_repos


def _make_repo_lookup(include_locals):
    data = {}
    for entry in get_global_repositories_data().items():
        if entry['enabled']:
            data.update({entry['id']: entry['path']})

    if include_locals:
        # Having it here allows to override global repositories with local ones.
        data.update(get_user_config_repo_data()['repos'])

    return data


def _resolve_repository_links(manager, include_locals):
    repo_lookup = _make_repo_lookup(include_locals=include_locals)
    finished = False
    while not finished:
        missing = manager.get_missing_repo_links()
        for repo_id in missing:
            if repo_id in repo_lookup:
                manager.add_repo(scan_repo(repo_lookup[repo_id]))
                break
        else:
            finished = True

    if manager.get_missing_repo_links():
        raise RepositoryConfigurationError('Missing repositories detected: {}'.format(', '.join(missing)))


def find_and_scan_repositories(path, manager=None, include_locals=False):
    """
    Finds and scans all repositories found in the path and it will also resolve linked repositories.
    Using include_locals=True will additionally include user local repositories to be considered for
    resolving linked repositories.

    :param path: Path to scan for repositories
    :param manager: Optional repository manager to add found repos too
    :param include_locals: Should repositories linked be searched from the user local registry
    :return: repository manager instance (either passed through or a new instance if none was passed)
    """
    if os.path.exists(path):
        manager = manager or RepositoryManager()
        for repository in find_repos(path):
            manager.add_repo(scan_repo(repository))
        _resolve_repository_links(manager=manager, include_locals=include_locals)
    return manager


def scan_repo(path):
    """
    Scans all related repository resources

    :param path:
    :type path: str
    :return: repository
    """
    path = os.path.abspath(path)
    return scan(Repository(path), path)


def scan(repository, path):
    """
    Scans all repository resources

    :param repository:
    :type repository: :py:class:`leapp.repository.Repository`
    :param path: path to the repository
    :type path: str
    :return: instance of :py:class:`leapp.repository.Repository`
    """
    repository.log.debug("Scanning path %s", path)
    scan_tasks = (
        ('topics', scan_topics),
        ('models', scan_models),
        ('actors', scan_actors),
        ('tags', scan_tags),
        ('workflows', scan_workflows),
        ('files', scan_files),
        ('libraries', scan_libraries),
        ('tests', scan_tests),
        ('tools', scan_tools))

    dirs = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]
    for name, task in scan_tasks:
        if name in dirs:
            task(repository, os.path.join(path, name), path)
    return repository


def scan_topics(repo, path, repo_path):
    """
    Scans topics and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the topics
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.TOPIC, os.path.relpath(path, repo_path))


def scan_actors(repo, path, repo_path):
    """
    Scans actors and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the actors
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    for root, _, files in os.walk(path):
        for module in files:
            if module == 'actor.py':
                rel_path = os.path.relpath(root, repo_path)
                repo.add(DefinitionKind.ACTOR, scan(ActorDefinition(rel_path, repo_path, log=repo.log), root))


def scan_tags(repo, path, repo_path):
    """
    Scans tags and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the tags
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.TAG, os.path.relpath(path, repo_path))


def scan_models(repo, path, repo_path):
    """
    Scans models and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the models
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.MODEL, os.path.relpath(path, repo_path))


def scan_workflows(repo, path, repo_path):
    """
    Scans workflows and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the workflows
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.WORKFLOW, os.path.relpath(path, repo_path))


def scan_files(repo, path, repo_path):
    """
    Scans files and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the files
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    if os.listdir(path):
        repo.add(DefinitionKind.FILES, os.path.relpath(path, repo_path))


def scan_libraries(repo, path, repo_path):
    """
    Scans libraries and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the libraries
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    if os.listdir(path):
        repo.add(DefinitionKind.LIBRARIES, os.path.relpath(path, repo_path))


def scan_tools(repo, path, repo_path):
    """
    Scans tools and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the tools
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    if os.listdir(path):
        repo.add(DefinitionKind.TOOLS, os.path.relpath(path, repo_path))


def scan_tests(repo, path, repo_path):
    """
    Scans tests and adds them to the repository.

    :param repo: Instance of the repository
    :type repo: :py:class:`leapp.repository.Repository`
    :param path: path to the tests
    :type path: str
    :param repo_path: path to the repository
    :type repo_path: str
    """
    if os.listdir(path):
        repo.add(DefinitionKind.TESTS, os.path.relpath(path, repo_path))
