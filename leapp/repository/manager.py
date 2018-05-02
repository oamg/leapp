import itertools


class RepositoryManager(object):
    """
    Handles multiple loaded repositories
    """
    def __init__(self):
        self._repos = []

    def lookup_actor(self, name):
        """
        Finds actor in all loaded repositories

        :param name: Name of the actor
        :type name: str
        :return: None or Actor
        """
        for repo in self._repos:
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
        for repo in self._repos:
            workflow = repo.lookup_workflow(name)
            if workflow:
                return workflow
        return None

    def add_repo(self, repo):
        """
        Adds new repository to manager.

        :param repo: Repository that will be added (registered) 
        :type repo: :py:class:`leapp.repository.Repository`
        """
        self._repos.append(repo)

    @property
    def repos(self):
        """
        Returns a tuple of all repository instances
        """
        return tuple(self._repos)

    def load(self):
        """
        Loads all known repositories.
        """
        for repo in self._repos:
            repo.load()

    def dump(self):
        """
        :return: List of resources in all known repositories
        """
        return [repo.dump() for repo in self._repos]

    @property
    def actors(self):
        """
        :return: Tuple of all actors from all repositories
        """
        return tuple(itertools.chain(*[repo.actors for repo in self._repos]))

    @property
    def topics(self):
        """
        :return: Tuple of all topics from all repositories
        """
        return tuple(itertools.chain(*[repo.topics for repo in self._repos]))

    @property
    def models(self):
        """
        :return: Tuple of all models from all repositories
        """
        return tuple(itertools.chain(*[repo.models for repo in self._repos]))

    @property
    def tags(self):
        """
        :return: Tuple of all tags from all repositories
        """
        return tuple(itertools.chain(*[repo.tags for repo in self._repos]))

    @property
    def workflows(self):
        """
        :return: Tuple of all workflows from all repositories
        """
        return tuple(itertools.chain(*[repo.workflows for repo in self._repos]))

    @property
    def tools(self):
        """
        :return: Tuple of all tools from all repositories
        """
        return tuple(itertools.chain(*[repo.tools for repo in self._repos]))

    @property
    def libraries(self):
        """
        :return: Tuple of all libraries from all repositories
        """
        return tuple(itertools.chain(*[repo.libraries for repo in self._repos]))

    @property
    def files(self):
        """
        :return: Tuple of all files from all repositories
        """
        return tuple(itertools.chain(*[repo.files for repo in self._repos]))
