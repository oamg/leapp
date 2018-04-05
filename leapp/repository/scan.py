import os

from leapp.repository import Repository, DefinitionKind
from leapp.repository.actor_definition import ActorDefinition


def scan_repo(path):
    path = os.path.abspath(path)
    return scan(Repository(path), path)


def scan(repository, path):
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
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.TOPIC, os.path.relpath(path, repo_path))


def scan_actors(repo, path, repo_path):
    for root, _, files in os.walk(path):
        for module in files:
            if module == 'actor.py':
                rel_path = os.path.relpath(root, repo_path)
                repo.add(DefinitionKind.ACTOR, scan(ActorDefinition(rel_path, repo_path, log=repo.log), root))


def scan_tags(repo, path, repo_path):
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.TAG, os.path.relpath(path, repo_path))


def scan_models(repo, path, repo_path):
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.MODEL, os.path.relpath(path, repo_path))


def scan_workflows(repo, path, repo_path):
    for root, _, files in os.walk(path):
        for module in files:
            _, ext = os.path.splitext(module)
            if ext == '.py':
                path = os.path.join(root, module)
                repo.add(DefinitionKind.WORKFLOW, os.path.relpath(path, repo_path))


def scan_files(repo, path, repo_path):
    if os.listdir(path):
        repo.add(DefinitionKind.FILES, os.path.relpath(path, repo_path))


def scan_libraries(repo, path, repo_path):
    if os.listdir(path):
        repo.add(DefinitionKind.LIBRARIES, os.path.relpath(path, repo_path))


def scan_tools(repo, path, repo_path):
    if os.listdir(path):
        repo.add(DefinitionKind.TOOLS, os.path.relpath(path, repo_path))


def scan_tests(repo, path, repo_path):
    if os.listdir(path):
        repo.add(DefinitionKind.TESTS, os.path.relpath(path, repo_path))
