from logging import getLogger
import os
import pkgutil
import sys

from leapp.exceptions import RepoItemPathDoesNotExistError, UnsupportedDefinitionKindError
from leapp.models import get_models, resolve_model_references
import leapp.libraries.common  # noqa # pylint: disable=unused-import
from leapp.repository.actor_definition import ActorDefinition
from leapp.repository.definition import DefinitionKind
from leapp.tags import get_tags
from leapp.topics import get_topics
from leapp.utils.libraryfinder import LeappLibrariesFinder
from leapp.utils.repository import get_repository_id, get_repository_links, get_repository_name
import leapp.workflows
from leapp.workflows import get_workflows


class _LoadStage(object):
    INITIAL = 'initial'
    MODELS = 'models'
    LIBRARIES = 'libraries'
    ACTORS = 'actors'
    WORKFLOWS = 'workflows'


class Repository(object):
    """
    The Repository class represents a place where all resources (actors, models, tags, etc.) are defined. See the
    :doc:`Repository Directory Layout <../repository-dir-layout>`.
    """

    def __init__(self, directory):
        """
        :param directory: Path to the repository folder
        :type directory: str
        """
        self.name = get_repository_name(directory)
        self.log = getLogger('leapp.repository').getChild(self.name)
        self._repo_dir = directory
        self._repo_id = get_repository_id(directory)
        self._repo_links = get_repository_links(directory)
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
        # TODO: what's the behaviour in case of multiple actors of the same name?
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

    def load(self, resolve=True, stage=None, skip_actors_discovery=False):
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
            self._load_modules(self.tags, 'leapp.tags')
            self.log.debug("Loading topic modules")
            self._load_modules(self.topics, 'leapp.topics')

        if not stage or stage is _LoadStage.MODELS:
            self.log.debug("Loading model modules")
            self._load_modules(self.models, 'leapp.models')
            if resolve:
                resolve_model_references()

        if not stage or stage is _LoadStage.LIBRARIES:
            self.log.debug("Extending PATH for common tool paths")
            self._extend_environ_paths('PATH', self.tools)
            self.log.debug("Extending LEAPP_COMMON_TOOLS for common tool paths")
            self._extend_environ_paths('LEAPP_COMMON_TOOLS', self.tools)
            self.log.debug("Extending LEAPP_COMMON_FILES for common file paths")
            self._extend_environ_paths('LEAPP_COMMON_FILES', self.files)
            self.log.debug("Installing repository provided common libraries loader hook")
            sys.meta_path.append(LeappLibrariesFinder(module_prefix='leapp.libraries.common', paths=self.libraries))
            sys.meta_path.append(LeappLibrariesFinder(module_prefix='leapp.workflows.api', paths=self.apis))

        if not skip_actors_discovery:
            if not stage or stage is _LoadStage.ACTORS:
                self.log.debug("Running actor discovery")
                for actor in self.actors:
                    actor.discover()

        if not stage or stage is _LoadStage.WORKFLOWS:
            self.log.debug("Loading workflow modules")
            self._load_modules(self.workflows, 'leapp.workflows')

    def _load_modules(self, modules, prefix):
        """
        :param modules: Paths to modules of the same type to be imported
        :type list of str
        :param prefix: A prefix to be appended to module name in sys.modules
        :type str
        """
        directories = [os.path.join(self._repo_dir, os.path.dirname(module)) for module in modules]
        prefix = prefix + '.' if not prefix.endswith('.') else prefix
        for importer, name, ispkg in pkgutil.iter_modules(directories, prefix=prefix):
            importer.find_module(name).load_module(name)

    def serialize(self):
        """
        :return: Dictionary of all repository resources
        """
        def filtered_serialization(func, modules):
            result = []
            data = func()
            for entry in data:
                if os.path.abspath(sys.modules[entry.__module__].__file__.replace('.pyc', '.py')) in modules:
                    result.append(entry.serialize())
            return result

        def mapped_actor_data(data):
            data.update({
                'consumes': [model.__name__ for model in data.get('consumes', ())],
                'produces': [model.__name__ for model in data.get('produces', ())],
                'tags': [tag.__name__ for tag in data.get('tags', ())]
            })
            return data

        return {
            'repo_dir': self._repo_dir,
            'actors': [mapped_actor_data(a.serialize()) for a in self.actors],
            'apis': [dict([('path', path)]) for path in self.relative_paths(self.apis)],
            'topics': filtered_serialization(get_topics, self.topics),
            'models': filtered_serialization(get_models, self.models),
            'tags': filtered_serialization(get_tags, self.tags),
            'workflows': filtered_serialization(get_workflows, self.workflows),
            'tools': [dict([('path', path)]) for path in self.relative_paths(self.tools)],
            'files': [dict([('path', path)]) for path in self.relative_paths(self.files)],
            'libraries': [dict([('path', path)]) for path in self.relative_paths(self.libraries)]
        }

    def _extend_environ_paths(self, name, paths):
        os.environ[name] = ':'.join(os.environ.get(name, '').split(':') + list(
            os.path.join(self._repo_dir, path) for path in paths))

    def relative_paths(self, paths):
        """
        :return: Tuple of repository relative paths
        """
        return tuple(os.path.relpath(x, self._repo_dir) for x in paths)

    @property
    def actors(self):
        """
        :return: Tuple of actors in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.ACTOR, ()))

    @property
    def apis(self):
        """
        :return: Tuple of apis in the repository
        """
        return tuple(self._definitions.get(DefinitionKind.API, ()))

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
