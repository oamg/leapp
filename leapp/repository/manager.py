import itertools

from leapp.repository import _LoadStage


class RepositoryManager(object):
    """
    Handles multiple loaded repositories
    """
    def __init__(self):
        self._repos = {}

    def lookup_actor(self, name):
        """
        Finds actor in all loaded repositories

        :param name: Name of the actor
        :type name: str
        :return: None or Actor
        """
        for repo in self._repos.values():
            actor = repo.lookup_actor(name)
            if actor:
                return actor
        return None

    def lookup_workflow(self, name):
        """
        Finds workflow in all loaded repositories

        :param name: Name of the workflow
        :type name: str
        :return: None or Workflow
        """
        for repo in self._repos.values():
            workflow = repo.lookup_workflow(name)
            if workflow:
                return workflow
        return None

    def get_missing_repo_links(self):
        """
        Gathers all missing repository ids linked by the added repositories.

        :return: Set of missing repository ids.
        """
        missing = set()
        available = set(self._repos.keys())
        for repo in self._repos.values():
            missing.update(set(repo.repo_links).difference(available))
        return missing

    def add_repo(self, repo):
        """
        Adds new repository to manager.

        :param repo: Repository that will be added (registered)
        :type repo: :py:class:`leapp.repository.Repository`
        """
        self._repos[repo.repo_id] = repo

    @property
    def repos(self):
        """
        Returns a tuple of all repository instances
        """
        return tuple(self._repos.values())

    def repo_by_id(self, repo_id):
        """
        Looks up a repository by id
        :param repo_id: Repository id
        :return: Repository or None
        """
        return self._repos.get(repo_id, None)

    def load(self, resolve=True):
        """
        Loads all known repositories.

        :param resolve: Whether or not to perform the resolving of model references
        :type resolve: bool
        """
        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.INITIAL)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.MODELS)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.LIBRARIES)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.ACTORS)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.WORKFLOWS)

        if resolve:
            from leapp.models import resolve_model_references
            resolve_model_references()

    def dump(self):
        """
        :return: List of resources in all known repositories
        """
        return [repo.dump() for repo in self._repos.values()]

    @property
    def actors(self):
        """
        :return: Tuple of all actors from all repositories
        """
        return tuple(itertools.chain(*[repo.actors for repo in self._repos.values()]))

    @property
    def topics(self):
        """
        :return: Tuple of all topics from all repositories
        """
        return tuple(itertools.chain(*[repo.topics for repo in self._repos.values()]))

    @property
    def models(self):
        """
        :return: Tuple of all models from all repositories
        """
        return tuple(itertools.chain(*[repo.models for repo in self._repos.values()]))

    @property
    def tags(self):
        """
        :return: Tuple of all tags from all repositories
        """
        return tuple(itertools.chain(*[repo.tags for repo in self._repos.values()]))

    @property
    def workflows(self):
        """
        :return: Tuple of all workflows from all repositories
        """
        return tuple(itertools.chain(*[repo.workflows for repo in self._repos.values()]))

    @property
    def tools(self):
        """
        :return: Tuple of all tools from all repositories
        """
        return tuple(itertools.chain(*[repo.tools for repo in self._repos.values()]))

    @property
    def libraries(self):
        """
        :return: Tuple of all libraries from all repositories
        """
        return tuple(itertools.chain(*[repo.libraries for repo in self._repos.values()]))

    @property
    def files(self):
        """
        :return: Tuple of all files from all repositories
        """
        return tuple(itertools.chain(*[repo.files for repo in self._repos.values()]))
