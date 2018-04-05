import itertools


class RepositoryManager(object):
    def __init__(self):
        self._repos = []

    def add_repo(self, repo):
        self._repos.append(repo)

    @property
    def repos(self):
        pass

    def load(self):
        for repo in self._repos:
            repo.load()

    def dump(self):
        return [repo.dump() for repo in self._repos]

    def inject(self):
        for repo in self._repos:
            repo.inject()

    @property
    def actors(self):
        return tuple(itertools.chain(*[repo.actors for repo in self._repos]))

    @property
    def topics(self):
        return tuple(itertools.chain(*[repo.topics for repo in self._repos]))

    @property
    def models(self):
        return tuple(itertools.chain(*[repo.models for repo in self._repos]))

    @property
    def tags(self):
        return tuple(itertools.chain(*[repo.tags for repo in self._repos]))

    @property
    def workflows(self):
        return tuple(itertools.chain(*[repo.workflows for repo in self._repos]))

    @property
    def tools(self):
        return tuple(itertools.chain(*[repo.tools for repo in self._repos]))

    @property
    def libraries(self):
        return tuple(itertools.chain(*[repo.libraries for repo in self._repos]))

    @property
    def files(self):
        return tuple(itertools.chain(*[repo.files for repo in self._repos]))
