from contextlib import contextmanager
import logging
import os
from subprocess import check_output

import py
import pytest

from leapp.actors import Actor, get_actors
from leapp.libraries.stdlib import api
from leapp.messaging import BaseMessaging
from leapp.models import ApiTestConsume, ApiTestProduce
from leapp.repository.scan import scan_repo


logging.basicConfig(format='%(asctime)-15s %(clientip)s %(user)-8s %(message)s')


class _TestableMessaging(BaseMessaging):
    def __init__(self, stored=True):
        super(_TestableMessaging, self).__init__(stored=stored)
        self.produced = []
        self.errors = []

    def produce(self, model, actor):
        self.produced.append(model)
        return super(_TestableMessaging, self).produce(model, actor)

    def _process_message(self, message):
        pass

    def _perform_load(self, consumes):
        pass

    def _do_produce(self, model, actor, target, stored=True):
        if type(model).__name__ == 'ErrorModel':
            self.errors.append(model)
        return super(_TestableMessaging, self)._do_produce(model=model, actor=actor, target=target, stored=stored)


@pytest.fixture(scope='module')
def repository(leapp_forked):  # noqa; pylint: disable=unused-argument
    repository_path = py.path.local(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'actor-api-tests'))
    with repository_path.as_cwd():
        repo = scan_repo('.')
        repo.load(resolve=True)
        yield repo


@contextmanager
def _with_loaded_actor(repository, actor_name, messaging=None):
    definition = repository.lookup_actor(actor_name)
    with py.path.local(definition.full_path).as_cwd():
        # Ensure environmental cleanup after the test
        with definition.injected_context():
            # Load the actor class
            definition.load()
            # Lookup the actor class
            actor = [a for a in get_actors() if a.name == definition.name][0]
            yield (definition, actor(messaging=messaging, logger=logging.getLogger('root')))


@pytest.mark.parametrize("actor_name", ('first', 'second'))
def test_actor_api(repository, actor_name):
    with _with_loaded_actor(repository, actor_name) as (_unused, actor):
        # Ensure the current instance is exactly the current actor
        assert actor == Actor.current_instance
        assert actor == api.current_actor()
        assert api.current_logger() == actor.log


@pytest.mark.parametrize("actor_name", ('first', 'second'))
def test_actor_messaging_paths(leapp_forked, repository, actor_name):  # noqa; pylint: disable=unused-argument
    messaging = _TestableMessaging()
    with _with_loaded_actor(repository, actor_name, messaging) as (_unused, actor):
        messaging.feed(ApiTestConsume(data='prefilled'), actor)

        assert len(list(actor.consume(ApiTestConsume))) == 1
        assert next(actor.consume(ApiTestConsume)).data == 'prefilled'

        assert len(list(api.consume(ApiTestConsume))) == 1
        assert next(api.consume(ApiTestConsume)).data == 'prefilled'

        actor_message = 'Actor {} sent message via Actor'.format(actor_name)
        api_message = 'Actor {} sent message via API'.format(actor_name)

        actor.produce(ApiTestProduce(data=actor_message))
        assert messaging.produced.pop().data == actor_message

        api.produce(ApiTestProduce(data=api_message))
        assert messaging.produced.pop().data == api_message

        api.report_error("api error report", details={'source': 'api'})
        assert messaging.errors.pop().message.startswith("api ")
        actor.report_error("actor error report", details={'source': 'actor'})
        assert messaging.errors.pop().message.startswith("actor ")


@pytest.mark.parametrize("actor_name", ('first', 'second'))
def test_actor_all_files_paths(leapp_forked, repository, actor_name):  # noqa; pylint: disable=unused-argument
    with _with_loaded_actor(repository, actor_name) as (definition, actor):
        # API consistency verification
        assert api.files_paths() == actor.files_paths
        assert api.common_files_paths() == actor.common_files_paths
        assert api.actor_files_paths() == actor.actor_files_paths

        # Ensure environment and actor api results are the same
        assert ':'.join(actor.actor_files_paths) == os.getenv('LEAPP_FILES')
        assert ':'.join(actor.common_files_paths) == os.getenv('LEAPP_COMMON_FILES')
        assert ':'.join(actor.actor_tools_paths) == os.getenv('LEAPP_TOOLS')
        assert ':'.join(actor.common_tools_paths) == os.getenv('LEAPP_COMMON_TOOLS')

        # Here we must ensure that the sorted list of entries are correct
        assert sorted(actor.files_paths) == sorted(
            os.getenv('LEAPP_FILES').split(':') + os.getenv('LEAPP_COMMON_FILES').split(':'))

        assert sorted(actor.tools_paths) == sorted(
            os.getenv('LEAPP_TOOLS').split(':') + os.getenv('LEAPP_COMMON_TOOLS').split(':'))

        # Ensure LEAPP_FILES/actor_files_paths are really actor private
        for directory in actor.actor_files_paths:
            assert directory.startswith(definition.full_path)

        # Ensure the duplicate is resolvable from the actor private files and the right file
        assert actor.get_actor_file_path('duplicate')
        with open(actor.get_actor_file_path('duplicate')) as f:
            assert f.read().strip() == actor_name + '-actor'

        # Do the same thing with the API
        assert api.get_actor_file_path('duplicate')
        with open(api.get_actor_file_path('duplicate')) as f:
            assert f.read().strip() == actor_name + '-actor'

        # Ensure the duplicate is resolvable from the repository files and the right file
        assert actor.get_common_file_path('duplicate')
        with open(actor.get_common_file_path('duplicate')) as f:
            assert f.read().strip() == 'repository'

        # Do the same thing with the API
        assert api.get_common_file_path('duplicate')
        with open(api.get_common_file_path('duplicate')) as f:
            assert f.read().strip() == 'repository'

        # Ensure tools files api
        assert api.get_common_tool_path('directory/exec_script')
        assert check_output(api.get_common_tool_path('directory/exec_script')).decode('utf-8').strip() == 'repository'
        assert not api.get_common_tool_path('directory/nonexec_script')

        assert api.get_actor_tool_path('directory/exec_script')
        assert check_output(api.get_actor_tool_path('directory/exec_script'))\
            .decode('utf-8').strip() == actor_name + '-actor'
        assert not api.get_actor_tool_path('directory/nonexec_script')

        # Ensure some file is resolvable from the repository files or the actor private files
        assert actor.get_file_path('duplicate')
        assert actor.get_file_path('duplicate') == api.get_file_path('duplicate')

        check_path = 'directory/{}-actor'.format(actor_name)
        assert actor.get_file_path(check_path)
        assert api.get_file_path(check_path) == actor.get_file_path(check_path)

        assert actor.get_file_path('directory/repository')
        assert api.get_file_path('directory/repository') == actor.get_file_path('directory/repository')

        assert not actor.get_common_file_path('directory/{}-actor'.format(actor_name))
        assert not api.get_common_file_path('directory/{}-actor'.format(actor_name))

        assert not actor.get_actor_file_path('directory/repository')
        assert not api.get_actor_file_path('directory/repository')
