import contextlib
import logging
import os
import pkgutil
import sys
from multiprocessing import Process, Queue

import leapp.libraries.actor
from leapp.actors import get_actors, get_actor_metadata
from leapp.exceptions import ActorInspectionFailedError, MultipleActorsError, UnsupportedDefinitionKindError
from leapp.repository import DefinitionKind
from leapp.repository.loader import library_loader


def inspect_actor(definition, result_queue):
    definition.load()
    result_queue.put([get_actor_metadata(actor) for actor in get_actors()])


class ActorCallContext(object):
    def __init__(self, definition, logger, messaging):
        self.definition = definition
        self.logger = logger
        self.messaging = messaging

    @staticmethod
    def _do_run(logger, messaging, definition, args, kwargs):
        definition.load()
        get_actors()[0](logger=logger, messaging=messaging).run(*args, **kwargs)

    def run(self, *args, **kwargs):
        p = Process(target=self._do_run, args=(self.logger, self.messaging, self.definition, args, kwargs))
        p.start()
        p.join()


class ActorDefinition(object):
    def __init__(self, directory, repo_dir, log=None):
        self.log = log or logging.getLogger('leapp.actor')
        self._directory = directory
        self._repo_dir = repo_dir
        self._definitions = {}
        self._module = None
        self._discovery = None

    def add(self, kind, path):
        if kind not in DefinitionKind.ACTOR_WHITELIST:
            self.log.error("Attempt to add item type %s to actor that is not supported", kind.name)
            raise UnsupportedDefinitionKindError('Actors do not support {kind}.'.format(kind=kind.name))
        self._definitions.setdefault(kind, []).append(path)

    def dump(self):
        return {
            'path': self.directory,
            'name': self.name,
            'tools': self.tools,
            'files': self.files,
            'libraries': self.libraries,
            'tests': self.tests
        }

    def load(self):
        if not self._module:
            with self.injected_context():
                path = os.path.abspath(os.path.join(self._repo_dir, self.directory))
                for importer, name, is_pkg in pkgutil.iter_modules((path,)):
                    if not is_pkg:
                        self._module = importer.find_module(name).load_module(name)
                        break

    def discover(self):
        if not self._discovery:
            self.log.debug("Starting actor discovery in %s", self.directory)
            q = Queue(1)
            p = Process(target=inspect_actor, args=(self, q))
            p.start()
            p.join()
            if p.exitcode != 0:
                self.log.error("Process inspecting actor in %s failed with %d", self.directory, p.exitcode)
                raise ActorInspectionFailedError('Inspection of actor in {path} failed'.format(path=self.directory))
            result = q.get()
            if not result:
                self.log.error("Process inspecting actor in %s returned no result", self.directory)
                raise ActorInspectionFailedError(
                    'Inspection of actor in {path} produced no results'.format(path=self.directory))
            if len(result) > 1:
                self.log.error("Actor in %s returned multiple actors", self.directory)
                raise MultipleActorsError(self.directory)
            self._discovery = result[0]
            for tag in self._discovery['tags']:
                if self not in tag.actors:
                    tag.actors += (self,)
        return self._discovery

    def __call__(self, messaging=None, logger=None):
        return ActorCallContext(definition=self, messaging=messaging, logger=logger)

    @property
    def consumes(self):
        return self.discover()['consumes']

    @property
    def produces(self):
        return self.discover()['produces']

    @property
    def class_name(self):
        return self.discover()['class_name']

    @property
    def name(self):
        return self.discover()['name']

    @property
    def description(self):
        return self.discover()['description']

    @contextlib.contextmanager
    def injected_context(self):

        # Backup of the path variable
        path_backup = os.environ.get('PATH', '')
        os.environ['PATH'] = ':'.join(path_backup.split(':') + list(self.tools))

        files_backup = os.environ.get('LEAPP_FILES', '')
        os.environ['LEAPP_FILES'] = ':'.join(files_backup.split(':') + list(self.files))

        # We make a snapshot of the symbols in the module
        before = leapp.libraries.actor.__dict__.keys()
        # Now we are loading all modules and packages and injecting them at the same time into the modules at hand
        to_add = library_loader(leapp.libraries.actor, 'leapp.libraries.actor',
                                map(lambda x: os.path.join(self._repo_dir, self.directory, x), self.libraries))
        backup = {}

        # Now we are injecting them into the global sys.modules dictionary and keep a backup of existing ones
        # The backup shouldn't be necessary, but just in case
        for name, mod in to_add:
            if name in sys.modules:
                backup[name] = sys.modules[name]
            sys.modules[name] = mod

        try:
            yield
        finally:

            # Restoration of the PATH environment variable
            os.environ['PATH'] = path_backup
            # Restoration of the LEAPP_FILES environment variable
            os.environ['LEAPP_FILES'] = files_backup

            # Remove all symbols in the actor lib before the execution
            current = leapp.libraries.actor.__dict__.keys()
            added = set(current).difference(before)
            for symbol in added:
                leapp.libraries.actor.__dict__.pop(symbol)

            # Remove all modules from the sys.modules dict or restore from backup if it was there
            for name, _ in to_add:
                if name in backup:
                    sys.modules[name] = backup[name]
                else:
                    sys.modules.pop(name)

    @property
    def directory(self):
        return self._directory

    @property
    def tools(self):
        return tuple(self._definitions.get(DefinitionKind.TOOLS, ()))

    @property
    def libraries(self):
        return tuple(self._definitions.get(DefinitionKind.LIBRARIES, ()))

    @property
    def files(self):
        return tuple(self._definitions.get(DefinitionKind.FILES, ()))

    @property
    def tests(self):
        return tuple(self._definitions.get(DefinitionKind.TESTS, ()))
