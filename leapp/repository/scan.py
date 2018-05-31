import os
import subprocess

from leapp.repository import Repository, DefinitionKind
from leapp.repository.manager import RepositoryManager
from leapp.repository.actor_definition import ActorDefinition


def find_and_scan_repositories(path, manager=None):
    if os.path.exists(path):
        manager = manager or RepositoryManager()
        result = subprocess.check_output(['/usr/bin/find', '-L', path, '-name', '.leapp']).decode('utf-8')
        for directory in result.strip().split('\n'):
            manager.add_repo(scan_repo(os.path.dirname(os.path.realpath(directory))))
    return manager


def scan_repo(path):
    """
    Scans all related repository resources

    :param path: path to the repository
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
