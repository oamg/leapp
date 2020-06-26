import os
import socket
import sys
import types
import uuid
from multiprocessing import Process, Queue

import pytest
from _pytest.python import pytest_pyfunc_call as original_pytest_pyfunc_call

from leapp.compat import raise_with_traceback
from leapp.messaging.inprocess import InProcessMessaging
from leapp.repository.scan import find_and_scan_repositories
from leapp.utils import get_api_models
from leapp.utils.audit import Execution, get_connection
from leapp.utils.repository import find_repository_basedir


PY27 = sys.version_info[:2] == (2, 7)
PY36 = sys.version_info[:2] == (3, 6)
PY38 = sys.version_info[:2] == (3, 8)
HIGHER = sys.version_info[:2] > (3, 8)


def _patched_name_py27(code, name):
    return types.CodeType(
        code.co_argcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        code.co_consts,
        code.co_names,
        code.co_varnames,
        code.co_filename,
        name,
        code.co_firstlineno,
        code.co_lnotab,
        code.co_freevars,
        code.co_cellvars,
    )


def _patched_name_py36(code, name):
    return types.CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        code.co_consts,
        code.co_names,
        code.co_varnames,
        code.co_filename,
        name,
        code.co_firstlineno,
        code.co_lnotab,
        code.co_freevars,
        code.co_cellvars,

    )


def _patched_name_py38(code, name):
    code.replace(co_name=name)
    return code


def _tb_pack(tb):
    result = []
    while tb is not None:
        code = tb.tb_frame.f_code
        result.append((code.co_filename, tb.tb_lineno, code.co_name))
        tb = tb.tb_next
    return result


def _tb_unpack(packed):
    previous = '_e'
    globs = {previous: StopIteration}
    for i, (filename, lineno, name) in enumerate(reversed(packed)):
        current = '_%d' % i
        eval(compile(  # noqa; pylint: disable=eval-used
            '%sdef %s(): raise %s()' % ('\n' * (lineno - 1), current, previous), filename, 'exec'), globs)
        previous = current
        func = globs[current]
        if PY27:
            func.func_code = _patched_name_py27(func.func_code, name)
        elif PY36:
            func.__code__ = _patched_name_py36(func.__code__, name)
        elif PY38 or HIGHER:
            func.__code__ = _patched_name_py38(func.__code__, name)
        else:
            raise NotImplementedError(
                "Traceback forwarding is not implemented for your"
                " Python version. Currently supported 2.7, 3.6, 3.8"
                " and higher"
            )
    try:
        globs[previous]()
    except StopIteration:
        globs.clear()
        return sys.exc_info()[2].tb_next


class ActorContext(object):
    """
    ActorContext is a helper class for testing actors. It helps to eliminate the boilerplate for executing
    actors. It provides a set of methods that allow specifying input messages for the actor, executing the
    actor and to retrieve messages sent by the actor.
    """
    apis = ()

    def __init__(self, actor=None):
        self._actor = actor
        self._messaging = InProcessMessaging()

    def set_actor(self, actor):
        """
        Internally used method to set the current actor specification object to setup the current actor for the
        test function.

        :param actor: ActorSpecification instance to use.
        :return: None
        """
        type(self).name = actor.name + '_feeder'
        # Consumes is here what it actually produces because we want to consume produced messages in 'consume'
        type(self).consumes = get_api_models(actor, 'produces')
        self._actor = actor

    def feed(self, *models):
        """
        Feed the messaging model with messages to be available to consume.

        :param models: Data in form of model instances to be available for the actor to consume.
        :type models: Variable number of instances of classes derived from :py:class:`leapp.models.Model`

        :return: None
        """
        for model in models:
            self._messaging.feed(model, self)

    def run(self, config_model=None):
        """
        Execute the current actor.

        :param config_model: Config model for the actor to consume.
        :type config_model: Config model instance derived from :py:class:`leapp.models.Model`
        :return: None
        """
        config_model_cls = config_model.__class__ if config_model else None
        if config_model:
            self._messaging.feed(config_model, self)
            # we have to make messaging system aware of config model being used as this is normally done by workflow
            self._messaging._config_models = (config_model_cls,)
        # the same as above applies here for actor
        self._actor(messaging=self._messaging, config_model=config_model_cls).run()

    def messages(self):
        """
        Returns raw messages produced by the actor.

        :return: list of raw message data dictionaries.
        """
        return self._messaging.messages()

    def consume(self, *models):
        """
        Retrieve messages produced by the actor execution and specified in the actors :py:attr:`produces`
        attribute, and filter message types by models.

        :param models: Models to use as a filter for the messages to return
        :type models: Variable number of the derived classes from :py:class:`leapp.models.Model`
        :return:
        """
        return tuple(self._messaging.consume(self, *models))


@pytest.fixture(scope='module')
def loaded_leapp_repository(request):
    """
    This fixture will ensure that the repository for the current test run is loaded with all its links etc.

    This enables running actors and using models, tags, topics, workflows etc.

    Additionally loaded_leapp_repository gives you access to a :py:class:`leapp.repository.manager.RepositoryManager`
    instance.

    :Example:

    .. code-block:: python

        from leapp.snactor.fixture import loaded_leapp_repository
        from leapp.models import ExampleModel, ProcessedExampleModel

        def my_repository_library_test(loaded_leapp_repository):
            from leapp.libraries.common import global
            e = ExampleModel(value='Some string')
            result = global.process_function(e)
            assert type(result) is ProcessedExampleModel

    """
    repository_path = find_repository_basedir(request.module.__file__)
    os.environ['LEAPP_CONFIG'] = os.path.join(repository_path, '.leapp', 'leapp.conf')
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    context = str(uuid.uuid4())
    with get_connection(None):
        Execution(context=context, kind='snactor-test-run', configuration='').store()
        os.environ["LEAPP_EXECUTION_ID"] = context

        manager = getattr(request.session, 'leapp_repository', None)
        if not manager:
            manager = find_and_scan_repositories(repository_path, include_locals=True)
            manager.load(resolve=True)
        yield manager


@pytest.fixture(scope='function')
def current_actor_context(loaded_leapp_repository):
    """
    This fixture will prepare an environment for the actor the test belongs to, to be safely executable.

    current_actor_context Is an instance of :py:class:`leapp.snactor.fixture.ActorContext` and gives access
    to its methods for feeding an actor with input data, running the actor, and retrieving messages produced
    by the actor during its execution.


    :Example:

    .. code-block:: python

        from leapp.snactor.fixture import current_actor_context
        from leapp.models import ConsumedExampleModel, ProducedExampleModel

        def test_actor_lib_some_function(current_actor_context):
            # Feed with messages to be consumable by the actor that is going to be executed.
            current_actor_context.feed(ConsumedExampleModel(value='Some random data'))

            # Execute the actor
            current_actor_context.run()

            # Ensure that at least one message is produced
            assert current_actor_context.consume(ProducedExampleModel)

            # Ensure the value is what we expect
            assert current_actor_context.consume(ProducedExampleModel)[0].value == 42
    """
    return type('CurrentActorContext', (ActorContext,), {'repository': loaded_leapp_repository, 'name': None})()


@pytest.fixture(scope='function')
def current_actor_libraries(request, loaded_leapp_repository):
    """
    This fixture will make libraries that are private to the actor only available only for the scope of the
    test function that uses this fixture.

    :Example:

    .. code-block:: python

        from leapp.snactor.fixture import current_actor_libraries

        def test_actor_lib_some_function(current_actor_libraries):
            from leapp.libraries.actor import private
            assert private.some_function(1) == 42

    """
    actor = _get_actor(request.module, loaded_leapp_repository)
    with actor.injected_context():
        yield actor


def _get_actor(module, repository):
    """
    Looks up the current actor based on the module passed. With help of the location of the module where
    the tests reside, the actor that is requested can be deduced since the full path of the actor should be
    the prefix of the path for the current test module.

    :param module: A python module object in which reside the tests for the actor to be run.
    :param repository: Instance of a :py:class:`leapp.repository.manager.RepositoryManager`
    :return: ActorDefinition instance or None, when the actor could not be found
    """
    path = os.path.realpath(module.__file__)
    for actor in repository.actors:
        if path.startswith(os.path.realpath(actor.full_path) + os.sep):
            return actor
    return None


@pytest.fixture(scope='module')
def leapp_forked():
    pass


def _execute_test(q, pyfuncitem):
    """
    This function is called in the child process from pytest_pyfunc_call via multiprocessing.Process.

    :param q: A multiprocessing.Queue object to pass data to the parent process
    :param pyfuncitem: pytest item describing the current test function
    :return: None
    """
    try:
        if 'current_actor_context' in pyfuncitem.funcargs:
            actor = _get_actor(pyfuncitem.module, pyfuncitem.funcargs['current_actor_context'].repository)
            pyfuncitem.funcargs['current_actor_context'].set_actor(actor)
        original_pytest_pyfunc_call(pyfuncitem=pyfuncitem)
        q.put((True, None))
    except BaseException:  # noqa; pylint: disable=broad-except
        # We need this broad exception to catch all errors and pass them through to the parent process
        e_type, e_exc, e_tb = sys.exc_info()
        q.put((False, (e_type, e_exc, _tb_pack(e_tb))))


if hasattr(pytest, 'hookimpl'):
    @pytest.hookimpl(tryfirst=True)
    def pytest_pyfunc_call(pyfuncitem):
        """
        This function is a hook for pytest implementing the ability to run the actors in tests safely.

        It will call :py:func:`leapp.snactor.fixture._execute_test` in a child process if the current test uses the
        :py:func:`current_actor_context` fixture. If it doesn't use the :py:func:`current_actor_context` fixture, it
        will default to the default `pytest_pyfunc_call` implementation.
        """
        if not any([arg in pyfuncitem.funcargs for arg in ('current_actor_context', 'leapp_forked')]):
            return None
        q = Queue()
        p = Process(target=_execute_test, args=(q, pyfuncitem))
        p.start()
        p.join()

        # Ensure we are actually getting a result - Otherwise ensure this is marked as failure
        assert not q.empty()
        r, e = q.get()
        if e:
            raise_with_traceback(e[1], _tb_unpack(e[2]))
        return r
