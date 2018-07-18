import os
import pkgutil
import sys


import leapp.libraries.common
import leapp.workflows
from logging import getLogger
from leapp.exceptions import ModuleNameAlreadyExistsError, RepoItemPathDoesNotExistError, UnsupportedDefinitionKindError
from leapp.repository.definition import DefinitionKind
from leapp.repository.actor_definition import ActorDefinition
from leapp.utils.project import get_project_name, get_project_id, get_project_repo_links


class _LoadStage(object):
    INITIAL = 'initial'
    MODELS = 'models'
    LIBRARIES = 'libraries'
    ACTORS = 'actors'
    WORKFLOWS = 'workflows'


class Repository(object):
    """
    The Repository class represents a place where all resources (actors, models, tags, etc.) are defined. The
    repository directory layout looks like:
    :ref:`Repository Directory Layout <best-practises:repository directory layout>`
    """
    def __init__(self, directory):
        """
        :param directory: Path to the repository folder
        :type directory: str
        """
        self.name = get_project_name(directory)
        self.log = getLogger('leapp.repository').getChild(self.name)
        self._repo_dir = directory
        self._repo_id = get_project_id(directory)
        self._repo_links = get_project_repo_links(directory)
        self._definitions = {}
        self.log.info("A new repository '%s' is initialized at %s", self.name, directory)

    @property
    def repo_dir(self):
        return self._repo_dir

    @property
    def repo_id(self):
        return self._repo_id

    @property
    def repo_links(self):
        return self._repo_links

    def lookup_actor(self, name):
        """
        Finds an actor in the repository

        :param name: Name of the actor
        :type name: str
        :return: None or Actor
        """
        name = name.lower()
        for actor in self.actors:
            actor_name = actor.name.lower()
            actor_class = actor.class_name.lower()
            if name in (actor_name, actor_class):
                return actor
        return None

    @staticmethod
    def lookup_workflow(name):
        """
        Finds a workflow in the repository

        :param name: Name of the workflow class name, Workflow.name, or Workflow.short_name
        :type name: str
        :return: None or Workflow
        """
        name = name.lower()
        for workflow in leapp.workflows.get_workflows():
            workflow_name = workflow.name.lower()
            workflow_class = workflow.__name__.lower()
            workflow_short_name = workflow.short_name
            if name in (workflow_name, workflow_class, workflow_short_name):
                return workflow
        return None

    def add(self, kind, item):
        """
        Adds any supported kind of a resource to the repository

        :param kind: specific kind of the repository resource
        :type kind: :py:class:`leapp.repository.definition.DefinitionKind`
        :param item: Item that will be added
        :type item: :py:class:`leapp.repository.actor_definition.ActorDefiniton` or str
        """
        self.log.debug('Adding %s - %s', kind.name, item.directory if isinstance(item, ActorDefinition) else item)
        if kind not in DefinitionKind.REPO_WHITELIST:
            raise UnsupportedDefinitionKindError('Repositories do not support {kind}.'.format(kind=kind.name))

        # Except for ActorDefinitions all items added are paths and are supposed to be relative paths to the repository
        if not isinstance(item, ActorDefinition):
            full_path = os.path.join(self._repo_dir, item)
            if not os.path.exists(full_path):
                self.log.error("Attempted to add %s, which is not in the repositories path", item)
                raise RepoItemPathDoesNotExistError(kind, item, full_path)
            item = full_path

        self._definitions.setdefault(kind, []).append(item)

    def load(self, resolve=True, stage=None):
        """
        Loads the repository resources

        :param resolve: Decides whether or not to perform the resolving of model references
        :type resolve: bool
        :param stage: Stage to load - Required for repository managers
        :type stage: _LoadStage value
        """
        if not stage or stage is _LoadStage.INITIAL:
            self.log.debug("Loading repository %s", self.name)
            self.log.debug("Loading tag modules")
            self._load_modules(self.tags)
            self.log.debug("Loading topic modules")
            self._load_modules(self.topics)

        if not stage or stage is _LoadStage.MODELS:
            self.log.debug("Loading model modules")
            self._load_modules(self.models)
            if resolve:
                from leapp.models import resolve_model_references
                resolve_model_references()

        if not stage or stage is _LoadStage.LIBRARIES:
            self.log.debug("Extending PATH for common tool paths")
            self._extend_environ_paths('PATH', self.tools)
            self.log.debug("Extending LEAPP_COMMON_FILES for common file paths")
            self._extend_environ_paths('LEAPP_COMMON_FILES', self.files)

            if not leapp.libraries.common.LEAPP_BUILTIN_COMMON_INITIALIZED:
                self.log.debug("Loading built-in common libraries")
                self._load_libraries(path=(os.path.dirname(leapp.libraries.common.__file__) + '/',))
                leapp.libraries.common.LEAPP_BUILTIN_COMMON_INITIALIZED = True

            self.log.debug("Loading repository provided common libraries")
            self._load_libraries()

        if not stage or stage is _LoadStage.ACTORS:
            self.log.debug("Running actor discovery")
            for actor in self.actors:
                actor.discover()

        if not stage or stage is _LoadStage.WORKFLOWS:
            self.log.debug("Loading workflow modules")
            self._load_modules(self.workflows)

    def _load_libraries(self, path=None, mod=None, prefix='leapp.libraries.common'):
        for importer, name, is_pkg in pkgutil.iter_modules(path or self.libraries):
            mod_full_name = prefix + '.' + name
            if mod_full_name in sys.modules:
                self.log.error("Common library module name clash: %s has been already loaded", mod_full_name)
                raise ModuleNameAlreadyExistsError(
                    'The {name} module has been already loaded from somewhere else.\n'
                    'Loaded: {loaded}\nNow: {now}'.format(
                        name=mod_full_name,
                        loaded=sys.modules.get(mod_full_name).__file__,
                        now=importer.find_module(name).file.name))
            loaded = importer.find_module(name).load_module(name)
            if not mod:
                setattr(leapp.libraries.common, name, loaded)
            sys.modules[mod_full_name] = loaded
            if is_pkg:
                self._load_libraries(path=(os.path.dirname(loaded.__file__),), mod=loaded, prefix=mod_full_name)

    def _load_modules(self, modules):
        directories = tuple(os.path.join(self._repo_dir, os.path.dirname(module)) for module in modules)
        for importer, name, is_pkg in pkgutil.iter_modules(directories):
            importer.find_module(name).load_module(name)

    def dump(self):
        """
        :return: Dictionary of all repository resources
        """
        return {
            'repo_dir': self._repo_dir,
            'actors': [a.dump() for a in self.actors],
            'topics': self.relative_paths(self.topics),
            'models': self.relative_paths(self.models),
            'tags': self.relative_paths(self.tags),
            'workflows': self.relative_paths(self.workflows),
            'tools': self.relative_paths(self.tools),
            'files': self.relative_paths(self.files),
            'libraries': self.relative_paths(self.libraries)
        }

    def _extend_environ_paths(self, name, paths):
        os.environ[name] = ':'.join(os.environ.get(name, '').split(':') +
                                    list(os.path.join(self._repo_dir, path) for path in paths))

    def relative_paths(self, paths):
        """
        :return: Tuple of repository relative paths
        """
        return tuple(map(lambda x: os.path.relpath(x, self._repo_dir), paths))

    @property
    def actors(self):
        """
        :return: Tuple of actors in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.ACTOR, ()))

    @property
    def topics(self):
        """
        :return: Tuple of topics in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.TOPIC, ()))

    @property
    def models(self):
        """
        :return: Tuple of models in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.MODEL, ()))

    @property
    def tags(self):
        """
        :return: Tuple of tags in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.TAG, ()))

    @property
    def workflows(self):
        """
        :return: Tuple of workflows in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.WORKFLOW, ()))

    @property
    def tools(self):
        """
        :return: Tuple of tools in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.TOOLS, ()))

    @property
    def libraries(self):
        """
        :return: Tuple of libraries in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.LIBRARIES, ()))

    @property
    def files(self):
        """
        :return: Tuple of files in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.FILES, ()))
