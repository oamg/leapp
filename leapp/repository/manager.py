import itertools

from leapp.models import resolve_model_references
from leapp.repository import _LoadStage


class RepositoryManager(object):
    """
    Handles multiple loaded repositories
    """

    def __init__(self):
        self._repos = {}

    def lookup_actor(self, name):
        """
        Find actor in all loaded repositories

        :param name: Name of the actor
        :type name: str
        :return: None or Actor
        """
        for repo in self._repos.values():
            actor = repo.lookup_actor(name)
            if actor:
                return actor
        return None

    def _lookup_actors(self, name):
        """
        Find all actors of the given name in all loaded repositories.

        Returns list of all actors of the given name in the loaded repositories
        or empty list.

        :param name: Name of the actor
        :type name: str
        :return: list
        """
        # FIXME: returns max 1 actor per repository (bug in the lookup_actor)
        actors = []
        for repo in self._repos.values():
            actor = repo.lookup_actor(name)
            if actor:
                actors.append(actor)
        return actors


    def lookup_workflow(self, name):
        """
        Find workflow in all loaded repositories

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
        Gather all missing repository ids linked by the added repositories.

        :return: Set of missing repository ids.
        """
        missing = set()
        available = set(self._repos.keys())
        for repo in self._repos.values():
            missing.update(set(repo.repo_links).difference(available))
        return missing

    def add_repo(self, repo):
        """
        Add new repository to manager.

        :param repo: Repository to be added (registered)
        :type repo: :py:class:`leapp.repository.Repository`
        """
        self._repos[repo.repo_id] = repo

    @property
    def repos(self):
        """
        :return: A tuple of all repository instances
        """
        return tuple(self._repos.values())

    def repo_by_id(self, repo_id):
        """
        Look up a repository by id

        :param repo_id: Repository id
        :return: Repository or None
        """
        return self._repos.get(repo_id, None)

    def load(self, resolve=True, skip_actors_discovery=False):
        """
        Load all known repositories.

        :param resolve: Whether or not to perform the resolving of model references
        :type resolve: bool
        :param skip_actors_discovery: specifies whether to skip discovery process of the actors
            When we testing actors, we're directly injecting the actor context, so we don't
            need to inject it during the repo loading. This option helps to solve this problem.
        :type skip_actors_discovery: bool
        """
        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.INITIAL)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.MODELS)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.LIBRARIES)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.ACTORS, skip_actors_discovery=skip_actors_discovery)

        for repo in self._repos.values():
            repo.load(resolve=False, stage=_LoadStage.WORKFLOWS)

        if resolve:
            resolve_model_references()

    def serialize(self):
        """
        :return: List of resources in all known repositories
        """
        return [repo.serialize() for repo in self._repos.values()]

    @property
    def actors(self):
        """
        :return: Tuple of :py:class:`leapp.repository.actor_definition.ActorDefinition` instances representing actors \
        from all repositories
        """
        return tuple(itertools.chain(*[repo.actors for repo in self._repos.values()]))

    @property
    def topics(self):
        """
        :return: Tuple of paths to topic-defining python modules from all repositories
        """
        return tuple(itertools.chain(*[repo.topics for repo in self._repos.values()]))

    @property
    def models(self):
        """
        :return: Tuple of paths to model-defining python modules from all repositories
        """
        return tuple(itertools.chain(*[repo.models for repo in self._repos.values()]))

    @property
    def tags(self):
        """
        :return: Tuple of paths to tag-defining python modules from all repositories
        """
        return tuple(itertools.chain(*[repo.tags for repo in self._repos.values()]))

    @property
    def workflows(self):
        """
        :return: Tuple of paths to workflow-defining python modules from all repositories
        """
        return tuple(itertools.chain(*[repo.workflows for repo in self._repos.values()]))

    @property
    def tools(self):
        """
        :return: Tuple of paths to "tools" folders from all repositories
        """
        return tuple(itertools.chain(*[repo.tools for repo in self._repos.values()]))

    @property
    def libraries(self):
        """
        :return: Tuple of paths to "libraries" folders from all repositories
        """
        return tuple(itertools.chain(*[repo.libraries for repo in self._repos.values()]))

    @property
    def files(self):
        """
        :return: Tuple of paths to "files" folders from all repositories
        """
        return tuple(itertools.chain(*[repo.files for repo in self._repos.values()]))
