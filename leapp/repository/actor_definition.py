import contextlib
import linecache
import logging
import os
import pkgutil
import sys
import traceback
import warnings
from io import UnsupportedOperation
from multiprocessing import Process, Queue, Pipe

import leapp.libraries.actor  # noqa # pylint: disable=unused-import
from leapp.actors import get_actor_metadata, get_actors
from leapp.exceptions import (ActorInspectionFailedError, LeappRuntimeError, MultipleActorsError,
                              UnsupportedDefinitionKindError)
from leapp.repository.definition import DefinitionKind
from leapp.utils.audit import create_audit_entry
from leapp.utils.deprecation import _LeappDeprecationWarning
from leapp.utils.libraryfinder import LeappLibrariesFinder


def inspect_actor(definition, result_queue):
    """
    Retrieves the actor information in a child process and returns the results back through `result_queue`.

    :param definition: the actor definition to load
    :type definition: :py:class:`ActorDefinition`
    :param result_queue: queue to pass results back to the calling process
    :type result_queue: :py:class:`multiprocessing.Queue`
    """
    definition.load()
    result = [get_actor_metadata(actor) for actor in get_actors()]
    result = [entry for entry in result if entry['path'] in definition.full_path]
    result_queue.put(result)


class ActorCallContext(object):
    """
    Wraps the actor execution into child process.
    """

    def __init__(self, definition, logger, messaging, config_model, skip_dialogs):
        """
        :param definition: Actor definition
        :type definition: :py:class:`leapp.repository.actor_definition.ActorDefinition`
        :param logger: Logger
        :type logger: :py:class:`logging.Logger`
        :param messaging: Leapp Messaging
        :type messaging: :py:class:`leapp.messaging.BaseMessaging`
        :param config_model: Workflow provided configuration model
        :type config_model: :py:class:`leapp.models.Model` derived class
        """
        self.definition = definition
        self.logger = logger
        self.messaging = messaging
        self.config_model = config_model
        self.skip_dialogs = skip_dialogs

    @staticmethod
    def _do_run(stdin, logger, messaging, definition, config_model, skip_dialogs, error_pipe, args, kwargs):
        if stdin is not None:
            try:
                sys.stdin = os.fdopen(stdin)
            except OSError:
                pass
        with warnings.catch_warnings(record=True) as recording:
            warnings.simplefilter(action="always", category=_LeappDeprecationWarning)
            definition.load()
            with definition.injected_context():
                target_actor = [actor for actor in get_actors() if actor.name == definition.name][0]
                actor_instance = target_actor(logger=logger, messaging=messaging, config_model=config_model,
                                              skip_dialogs=skip_dialogs)
                try:
                    actor_instance.run(*args, **kwargs)
                except Exception:
                    # Send the exception data string to the parent process
                    # and reraise.
                    error_pipe.send(traceback.format_exc())
                    raise
            try:
                # By this time this is no longer set, so we have to get it back
                os.environ['LEAPP_CURRENT_ACTOR'] = actor_instance.name
                for rec in recording:
                    if issubclass(rec.category, _LeappDeprecationWarning):
                        entry = {
                            'message': str(rec.message),
                            'filename': rec.filename,
                            'line': linecache.getline(rec.filename, rec.lineno) if rec.line is None else rec.line,
                            'lineno': rec.lineno,
                            'since': rec.category.since,
                            'reason': rec.category.msg
                        }
                        create_audit_entry('deprecation', entry)
            finally:
                # Remove it again
                os.environ.pop('LEAPP_CURRENT_ACTOR')

    def run(self, *args, **kwargs):
        """
        Performs the actor execution in the child process.
        """
        try:
            stdin = sys.stdin.fileno()
        except UnsupportedOperation:
            stdin = None

        pipe_receiver, pipe_sender = Pipe()
        p = Process(target=self._do_run,
                    args=(stdin, self.logger, self.messaging, self.definition, self.config_model,
                          self.skip_dialogs, pipe_sender, args, kwargs))
        p.start()
        p.join()
        if p.exitcode != 0:
            err_message = "Actor {actorname} unexpectedly terminated with exit code: {exitcode}".format(
                actorname=self.definition.name, exitcode=p.exitcode)

            exception_info = None
            # If there's data in the pipe, it's formatted exception info.
            if pipe_receiver.poll():
                exception_info = pipe_receiver.recv()

            # This LeappRuntimeError will contain an exception traceback
            # in addition to the above message.
            raise LeappRuntimeError(err_message, exception_info)


class ActorDefinition(object):
    """
    Defines actor resources.

    """

    def __init__(self, directory, repo_dir, log=None):
        """
        :param log: Logger
        :type log: :py:class:`logging.Logger`
        :param directory: Actor directory
        :type directory: str
        :param repo_dir: Repository directory
        :type repo_dir: str
        """
        self.log = log or logging.getLogger('leapp.actor')
        self._directory = directory
        self._repo_dir = repo_dir
        self._definitions = {}
        self._module = None
        self._discovery = None

    @property
    def full_path(self):
        return os.path.realpath(os.path.join(self._repo_dir, self._directory))

    def add(self, kind, path):
        """
        Adds any kind of actor resource to the Definition

        :param kind: kind of resource added
        :type kind: str
        :param path: path to the added resource
        :type path: str
        """
        if kind not in DefinitionKind.ACTOR_WHITELIST:
            self.log.error("Attempt to add item type %s to actor that is not supported", kind.name)
            raise UnsupportedDefinitionKindError('Actors do not support {kind}.'.format(kind=kind.name))
        self._definitions.setdefault(kind, []).append(path)

    def serialize(self):
        """
        :return: dump of actor resources (path, name, tools, files, libraries, tests)
        """
        return {
            'path': self.directory,
            'name': self.name,
            'class_name': self.class_name,
            'description': self.description,
            'tags': self.tags,
            'consumes': self.consumes,
            'produces': self.produces,
            'apis': self.apis,
            'dialogs': [dialog.serialize() for dialog in self.dialogs],
            'tools': self.tools,
            'files': self.files,
            'libraries': self.libraries,
            'tests': self.tests
        }

    def load(self):
        """
        Loads the actor module to be introspectable.
        """
        if not self._module:
            with self.injected_context():
                path = os.path.abspath(os.path.join(self._repo_dir, self.directory))
                for importer, name, is_pkg in pkgutil.iter_modules((path,)):
                    if not is_pkg:
                        self._module = importer.find_module(name).load_module(name)
                        break

    def discover(self):
        """
        Performs introspection through a subprocess.

        :return: Dictionary with discovered items.
        """
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

    def __call__(self, messaging=None, logger=None, config_model=None, skip_dialogs=False):
        return ActorCallContext(definition=self, messaging=messaging, logger=logger, config_model=config_model,
                                skip_dialogs=skip_dialogs)

    @property
    def dialogs(self):
        """
        :return: Tuple of defined dialogs
        """
        return self.discover()['dialogs']

    @property
    def consumes(self):
        """
        :return: Tuple of consumed models
        """
        return self.discover()['consumes']

    @property
    def produces(self):
        """
        :return: Tuple of produced models
        """
        return self.discover()['produces']

    @property
    def tags(self):
        """
        :return: Tuple of tags assigned to the actor
        """
        return self.discover()['tags']

    @property
    def class_name(self):
        """
        :return: Actor class name
        """
        return self.discover()['class_name']

    @property
    def name(self):
        """
        :return: Actor internal name
        """
        return self.discover()['name']

    @property
    def description(self):
        """
        :return: Actor description
        """
        return self.discover()['description']

    @contextlib.contextmanager
    def injected_context(self):
        """
        Prepares the actor environment for running the actor.
        This includes injecting actor private libraries into :py:mod:`leapp.libraries.actor`
        and setting environment variables for private tools and files.

        :note: Use with caution.
        """
        # Backup of the path variable
        path_backup = os.environ.get('PATH', '')
        os.environ['PATH'] = ':'.join(path_backup.split(':') + list(
            os.path.join(self._repo_dir, self._directory, path) for path in self.tools))

        files_backup = os.environ.get('LEAPP_FILES', None)
        if self.files:
            os.environ['LEAPP_FILES'] = os.path.join(self._repo_dir, self._directory, self.files[0])

        tools_backup = os.environ.get('LEAPP_TOOLS', None)
        if self.tools:
            os.environ['LEAPP_TOOLS'] = os.path.join(self._repo_dir, self._directory, self.tools[0])

        sys.meta_path.append(
            LeappLibrariesFinder(
                module_prefix='leapp.libraries.actor',
                paths=[os.path.join(self._repo_dir, self.directory, x) for x in self.libraries]))

        previous_path = os.getcwd()
        os.chdir(os.path.join(self._repo_dir, self._directory))
        try:
            yield
        finally:
            os.chdir(previous_path)

            # Restoration of the PATH environment variable
            os.environ['PATH'] = path_backup
            # Restoration of the LEAPP_FILES environment variable
            if files_backup is not None:
                os.environ['LEAPP_FILES'] = files_backup
            else:
                os.environ.pop('LEAPP_FILES', None)

            if tools_backup is not None:
                os.environ['LEAPP_TOOLS'] = tools_backup
            else:
                os.environ.pop('LEAPP_TOOLS', None)

    @property
    def apis(self):
        """
        :return: names of APIs used by this actor
        """
        return tuple(self.discover()['apis'])

    @property
    def directory(self):
        """
        :return: The folder path of the actor
        """
        return self._directory

    @property
    def tools(self):
        """
        :return: Tuple with path to the tools folder of the actor, empty tuple if none
        """
        return tuple(self._definitions.get(DefinitionKind.TOOLS, ()))

    @property
    def libraries(self):
        """
        :return: Tuple with path to the libraries folder of the actor, empty tuple if none
        """
        return tuple(self._definitions.get(DefinitionKind.LIBRARIES, ()))

    @property
    def files(self):
        """
        :return: Tuple with path to the files folder of the actor, empty tuple if none
        """
        return tuple(self._definitions.get(DefinitionKind.FILES, ()))

    @property
    def tests(self):
        """
        :return: Tuple with path to the tests folder of the actor, empty tuple if none
        """
        return tuple(self._definitions.get(DefinitionKind.TESTS, ()))
