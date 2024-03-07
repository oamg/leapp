import os
import json
import tempfile

import mock
import py
import pytest

from leapp.repository.scan import scan_repo
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent, ChoiceComponent, NumberComponent, TextComponent
from leapp.utils.audit import get_connection, dict_factory, store_dialog
from leapp.utils.audit import Dialog as DialogDB
from leapp.config import get_config

_HOSTNAME = 'test-host.example.com'
_CONTEXT_NAME = 'test-context-name-dialogdb'
_ACTOR_NAME = 'test-actor-name'
_PHASE_NAME = 'test-phase-name'
_DIALOG_SCOPE = 'test-dialog'

_TEXT_COMPONENT_METADATA = {
    'default': None,
    'description': 'a text value is needed',
    'key': 'text',
    'label': 'text',
    'reason': None,
    'value': None
}
_BOOLEAN_COMPONENT_METADATA = {
    'default': None,
    'description': 'a boolean value is needed',
    'key': 'bool',
    'label': 'bool',
    'reason': None,
    'value': None
}

_NUMBER_COMPONENT_METADATA = {
    'default': -1,
    'description': 'a numeric value is needed',
    'key': 'num',
    'label': 'num',
    'reason': None,
    'value': None
}
_CHOICE_COMPONENT_METADATA = {
    'default': None,
    'description': 'need to choose one of these choices',
    'key': 'choice',
    'label': 'choice',
    'reason': None,
    'value': None
}
_COMPONENT_METADATA = [
    _TEXT_COMPONENT_METADATA, _BOOLEAN_COMPONENT_METADATA, _NUMBER_COMPONENT_METADATA, _CHOICE_COMPONENT_METADATA
]
_COMPONENT_METADATA_FIELDS = ('default', 'description', 'key', 'label', 'reason', 'value')
_DIALOG_METADATA_FIELDS = ('answer', 'title', 'reason', 'components')

_TEST_DIALOG = Dialog(
    scope=_DIALOG_SCOPE,
    reason='need to test dialogs',
    components=(
        TextComponent(
            key='text',
            label='text',
            description='a text value is needed',
        ),
        BooleanComponent(key='bool', label='bool', description='a boolean value is needed'),
        NumberComponent(key='num', label='num', description='a numeric value is needed'),
        ChoiceComponent(
            key='choice',
            label='choice',
            description='need to choose one of these choices',
            choices=('One', 'Two', 'Three', 'Four', 'Five'),
        ),
    ),
)


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


def fetch_dialog(dialog_id=None):
    entry = None
    with get_connection(None) as conn:

        if dialog_id is not None:
            cursor = conn.execute('SELECT * FROM dialog WHERE id = ?;', (dialog_id,))
        else:    # Fetch last saved dialog
            cursor = conn.execute('SELECT * FROM dialog ORDER BY id DESC LIMIT 1;',)

        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    return entry


def test_save_empty_dialog():
    e = DialogDB(
        scope=_DIALOG_SCOPE,
        data=None,
        context=_CONTEXT_NAME,
        actor=_ACTOR_NAME,
        phase=_PHASE_NAME,
        hostname=_HOSTNAME,
    )
    e.store()

    assert e.dialog_id
    assert e.data_source_id
    assert e.host_id

    entry = fetch_dialog(e.dialog_id)
    assert entry is not None
    assert entry['data_source_id'] == e.data_source_id
    assert entry['context'] == _CONTEXT_NAME
    assert entry['scope'] == _DIALOG_SCOPE
    assert entry['data'] == 'null'


def test_save_dialog(monkeypatch):
    monkeypatch.setenv('LEAPP_CURRENT_ACTOR', _ACTOR_NAME)
    monkeypatch.setenv('LEAPP_CURRENT_PHASE', _PHASE_NAME)
    monkeypatch.setenv('LEAPP_EXECUTION_ID', _CONTEXT_NAME)
    monkeypatch.setenv('LEAPP_HOSTNAME', _HOSTNAME)
    e = store_dialog(_TEST_DIALOG, {})
    monkeypatch.delenv('LEAPP_CURRENT_ACTOR')
    monkeypatch.delenv('LEAPP_CURRENT_PHASE')
    monkeypatch.delenv('LEAPP_EXECUTION_ID')
    monkeypatch.delenv('LEAPP_HOSTNAME')

    entry = fetch_dialog(e.dialog_id)
    assert entry is not None
    assert entry['data_source_id'] == e.data_source_id
    assert entry['context'] == _CONTEXT_NAME
    assert entry['scope'] == _TEST_DIALOG.scope

    entry_data = json.loads(entry['data'])

    assert sorted(entry_data.keys()) == sorted(_DIALOG_METADATA_FIELDS)

    assert entry_data['answer'] == {}
    assert entry_data['reason'] == 'need to test dialogs'
    assert entry_data['title'] is None
    for component_metadata in _COMPONENT_METADATA:
        assert sorted(component_metadata.keys()) == sorted(_COMPONENT_METADATA_FIELDS)
        assert component_metadata in entry_data['components']


def test_save_dialog_workflow(monkeypatch, repository):
    workflow = repository.lookup_workflow('LeappDBUnitTest')()
    with tempfile.NamedTemporaryFile(mode='w') as stdin_dialog:
        monkeypatch.setenv('LEAPP_TEST_EXECUTION_LOG', '/dev/null')
        stdin_dialog.write('my answer\n')
        stdin_dialog.write('yes\n')
        stdin_dialog.write('42\n')
        stdin_dialog.write('0\n')
        stdin_dialog.seek(0)
        with mock.patch('sys.stdin.fileno', return_value=stdin_dialog.fileno()):
            workflow.run(skip_dialogs=False)

        monkeypatch.delenv('LEAPP_TEST_EXECUTION_LOG', '/dev/null')

    entry = fetch_dialog()
    assert entry is not None
    assert entry['scope'] == 'unique_dialog_scope'
    data = json.loads(entry['data'])
    assert data['answer'] == {'text': 'my answer', 'num': 42, 'bool': True, 'choice': 'One'}
