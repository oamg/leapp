import os
import json
import tempfile

import py
import pytest

from leapp.repository.scan import scan_repo
from leapp.config import get_config
from leapp.utils.audit import get_audit_entry

_HOSTNAME = 'test-host.example.com'
_CONTEXT_NAME = 'test-context-name-exit-status'
_ACTOR_NAME = 'test-actor-name'
_PHASE_NAME = 'test-phase-name'
_DIALOG_SCOPE = 'test-dialog'


@pytest.fixture(scope='module')
def repository():
    repository_path = py.path.local(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'leappdb-tests'))
    with repository_path.as_cwd():
        repo = scan_repo('.')
        repo.load(resolve=True)
        yield repo


def setup_module():
    get_config().set('database', 'path', '/tmp/leapp-test.db')


def setup():
    path = get_config().get('database', 'path')
    if os.path.isfile(path):
        os.unlink(path)


@pytest.mark.parametrize('error, code', [(None, 0), ('StopActorExecution', 0), ('StopActorExecutionError', 0),
                                         ('UnhandledError', 1)])
def test_exit_status_stopactorexecution(monkeypatch, repository, error, code):

    workflow = repository.lookup_workflow('LeappDBUnitTest')()

    if error is not None:
        os.environ['ExitStatusActor-Error'] = error
    else:
        os.environ.pop('ExitStatusActor-Error', None)

    with tempfile.NamedTemporaryFile() as test_log_file:
        monkeypatch.setenv('LEAPP_TEST_EXECUTION_LOG', test_log_file.name)
        monkeypatch.setenv('LEAPP_HOSTNAME', _HOSTNAME)
        try:
            workflow.run(skip_dialogs=True, context=_CONTEXT_NAME, until_actor='ExitStatusActor')
        except BaseException:  # pylint: disable=broad-except
            pass

    ans = get_audit_entry('actor-exit-status', _CONTEXT_NAME).pop()

    assert ans is not None
    assert ans['actor'] == 'exit_status_actor'
    assert ans['context'] == _CONTEXT_NAME
    assert ans['hostname'] == _HOSTNAME
    data = json.loads(ans['data'])
    assert data['exit_status'] == code


def teardown():
    os.environ.pop('ExitStatusActor-Error', None)
