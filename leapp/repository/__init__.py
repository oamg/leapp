import os
import pkgutil
import sys


import leapp.libraries.common
from logging import getLogger
from leapp.exceptions import ModuleNameAlreadyExistsError, RepoItemPathDoesNotExistError, UnsupportedDefinitionKindError
from leapp.repository.definition import DefinitionKind
from leapp.repository.actor_definition import ActorDefinition
from leapp.utils.project import get_project_name


class Repository(object):
    def __init__(self, directory):
        self.name = get_project_name(directory)
        self.log = getLogger('leapp.repository').getChild(self.name)
        self._repo_dir = directory
        self._definitions = {}
        self.log.info("New repository '%s' initialized at %s", self.name, directory)

    def lookup_actor(self, name):
        name = name.lower()
        for actor in self.actors:
            actor_name = actor.name.lower()
            actor_class = actor.class_name.lower()
            if actor_name == name or actor_class == name:
                return actor
        return None

    def add(self, kind, item):
        self.log.debug('Adding %s - %s', kind.name, item.directory if isinstance(item, ActorDefinition) else item)
        if kind not in DefinitionKind.REPO_WHITELIST:
            raise UnsupportedDefinitionKindError('Repositories do not support {kind}.'.format(kind=kind.name))

        # Except for ActorDefinitions all items added are paths and are supposed to be relative paths to the repository
        if not isinstance(item, ActorDefinition):
            full_path = os.path.join(self._repo_dir, item)
            if not os.path.exists(full_path):
                self.log.error("Attempted to add %s which is not in the repositories path", item)
                raise RepoItemPathDoesNotExistError(kind, item, full_path)
            item = full_path

        self._definitions.setdefault(kind, []).append(item)

    def load(self):
        self.log.debug("Loading repository %s", self.name)
        self.log.debug("Loading tag modules")
        self._load_modules(self.tags)
        self.log.debug("Loading topic modules")
        self._load_modules(self.topics)
        self.log.debug("Loading model modules")
        self._load_modules(self.models)

        if not leapp.libraries.common.LEAPP_BUILTIN_COMMON_INITIALIZED:
            self.log.debug("Loading builtin common libraries")
            self._load_libraries(path=(os.path.dirname(leapp.libraries.common.__file__) + '/',))
            leapp.libraries.common.LEAPP_BUILTIN_COMMON_INITIALIZED = True

        self.log.debug("Loading repository provided common libraries")
        self._load_libraries()

        self.log.debug("Extending PATH for common snactor paths")
        self._extend_environ_paths('PATH', self.tools)
        self.log.debug("Extending LEAPP_COMMON_FILES for common file paths")
        self._extend_environ_paths('LEAPP_COMMON_FILES', self.files)

        self.log.debug("Running actor discovery")
        for actor in self.actors:
            actor.discover()

        self.log.debug("Loading workflow modules")
        self._load_modules(self.workflows)

    def _load_libraries(self, path=None, mod=None, prefix='leapp.libraries.common'):
        for importer, name, is_pkg in pkgutil.iter_modules(path or self.libraries):
            mod_full_name = prefix + '.' + name
            if mod_full_name in sys.modules:
                self.log.error("Common library module name clash: %s has been already loaded", mod_full_name)
                raise ModuleNameAlreadyExistsError(
                    'Module {name} has been already loaded from somewhere else.\n'
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
        directories = {os.path.join(self._repo_dir, os.path.dirname(module)) for module in modules}
        for importer, name, is_pkg in pkgutil.iter_modules(directories):
            importer.find_module(name).load_module(name)

    def dump(self):
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

    @staticmethod
    def _extend_environ_paths(name, paths):
        os.environ[name] = ':'.join(os.environ.get(name, '').split(':') + list(paths))

    def relative_paths(self, paths):
        return map(lambda x: os.path.relpath(x, self._repo_dir), paths)

    @property
    def actors(self):
        return tuple(self._definitions.get(DefinitionKind.ACTOR, ()))

    @property
    def topics(self):
        return tuple(self._definitions.get(DefinitionKind.TOPIC, ()))

    @property
    def models(self):
        return tuple(self._definitions.get(DefinitionKind.MODEL, ()))

    @property
    def tags(self):
        return tuple(self._definitions.get(DefinitionKind.TAG, ()))

    @property
    def workflows(self):
        return tuple(self._definitions.get(DefinitionKind.WORKFLOW, ()))

    @property
    def tools(self):
        return tuple(self._definitions.get(DefinitionKind.TOOLS, ()))

    @property
    def libraries(self):
        return tuple(self._definitions.get(DefinitionKind.LIBRARIES, ()))

    @property
    def files(self):
        return tuple(self._definitions.get(DefinitionKind.FILES, ()))
