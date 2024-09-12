import os
import json
import logging
import hashlib

import mock
import py
import pytest

from leapp.repository.scan import scan_repo
from leapp.repository.actor_definition import ActorDefinition
from leapp.utils.audit import (get_connection, dict_factory, Metadata, Entity, store_actor_metadata,
                               store_workflow_metadata)
from leapp.config import get_config

_HOSTNAME = 'test-host.example.com'
_CONTEXT_NAME = 'test-context-name-metadata'
_ACTOR_NAME = 'test-actor-name'
_PHASE_NAME = 'test-phase-name'
_DIALOG_SCOPE = 'test-dialog'

_WORKFLOW_METADATA_FIELDS = ('description', 'name', 'phases', 'short_name', 'tag')
_ACTOR_METADATA_FIELDS = ('class_name', 'config_schemas', 'name', 'description',
                          'phase', 'tags', 'consumes', 'produces', 'path')

_TEST_WORKFLOW_METADATA = {
    'description': 'No description has been provided for the UnitTest workflow.',
    'name': 'LeappDBUnitTest',
    'phases': [{
        'class_name': 'FirstPhase',
        'filter': {
            'phase': 'FirstPhaseTag',
            'tags': ['UnitTestWorkflowTag']
        },
        'flags': {
            'is_checkpoint': False,
            'request_restart_after_phase': False,
            'restart_after_phase': False
        },
        'index': 4,
        'name': 'first-phase',
        'policies': {
            'error': 'FailImmediately',
            'retry': 'Phase'
        }
    }, {
        'class_name': 'SecondPhase',
        'filter': {
            'phase': 'SecondPhaseTag',
            'tags': ['UnitTestWorkflowTag']
        },
        'flags': {
            'is_checkpoint': False,
            'request_restart_after_phase': False,
            'restart_after_phase': False
        },
        'index': 5,
        'name': 'second-phase',
        'policies': {
            'error': 'FailPhase',
            'retry': 'Phase'
        }
    }],
    'short_name': 'unit_test',
    'tag': 'UnitTestWorkflowTag'
}
_TEST_ACTOR_METADATA = {
    'description': 'Test Description',
    'class_name': 'TestActor',
    'name': 'test-actor',
    'path': 'actors/test',
    'tags': (),
    'consumes': (),
    'produces': (),
    'dialogs': (),
    'apis': ()
}


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


def test_save_empty_metadata():
    hash_id = hashlib.sha256('test-empty-metadata'.encode('utf-8')).hexdigest()
    md = Metadata(hash_id=hash_id, metadata='')
    md.store()

    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute('SELECT * FROM metadata WHERE hash = ?;', (hash_id,))
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['metadata'] == ''


def test_save_empty_entity():
    hash_id = hashlib.sha256('test-empty-entity'.encode('utf-8')).hexdigest()
    md = Metadata(hash_id=hash_id, metadata='')
    e = Entity(
        name='test-name',
        metadata=md,
        kind='test-kind',
        context=_CONTEXT_NAME,
        hostname=_HOSTNAME,
    )
    e.store()

    assert e.entity_id
    assert e.host_id

    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute('SELECT * FROM entity WHERE id = ?;', (e.entity_id,))
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['kind'] == 'test-kind'
    assert entry['name'] == 'test-name'
    assert entry['context'] == _CONTEXT_NAME
    assert entry['metadata_hash'] == hash_id


def test_store_actor_metadata(monkeypatch, repository_dir):
    # ---
    # Test store actor metadata without error
    # ---
    with repository_dir.as_cwd():
        logger = logging.getLogger('leapp.actor.test')
        with mock.patch.object(logger, 'log') as log_mock, mock.patch('os.chdir'):
            definition = ActorDefinition('actors/test', '.', log=log_mock)
            with mock.patch('leapp.repository.actor_definition.get_actor_metadata', return_value=_TEST_ACTOR_METADATA):
                with mock.patch('leapp.repository.actor_definition.get_actors', return_value=[True]):
                    definition._module = True

                    monkeypatch.setenv('LEAPP_EXECUTION_ID', _CONTEXT_NAME)
                    monkeypatch.setenv('LEAPP_HOSTNAME', _HOSTNAME)
                    store_actor_metadata(definition, 'test-phase')
                    monkeypatch.delenv('LEAPP_EXECUTION_ID')
                    monkeypatch.delenv('LEAPP_HOSTNAME')

    # ---
    # Test retrieve correct actor metadata
    # ---
    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute('SELECT * '
                              'FROM entity '
                              'JOIN metadata '
                              'ON entity.metadata_hash = metadata.hash '
                              'WHERE name="test-actor";')
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['kind'] == 'actor'
    assert entry['name'] == _TEST_ACTOR_METADATA['name']
    assert entry['context'] == _CONTEXT_NAME

    metadata = json.loads(entry['metadata'])
    assert sorted(metadata.keys()) == sorted(_ACTOR_METADATA_FIELDS)
    assert metadata['class_name'] == _TEST_ACTOR_METADATA['class_name']
    assert metadata['name'] == _TEST_ACTOR_METADATA['name']
    assert metadata['description'] == _TEST_ACTOR_METADATA['description']
    assert metadata['phase'] == 'test-phase'
    assert sorted(metadata['tags']) == sorted(_TEST_ACTOR_METADATA['tags'])
    assert sorted(metadata['consumes']) == sorted(_TEST_ACTOR_METADATA['consumes'])
    assert sorted(metadata['produces']) == sorted(_TEST_ACTOR_METADATA['produces'])


def test_workflow_metadata(monkeypatch, repository):
    # ---
    # Test store workflow metadata without error
    # ---
    workflow = repository.lookup_workflow('LeappDBUnitTest')()

    monkeypatch.setenv('LEAPP_EXECUTION_ID', _CONTEXT_NAME)
    monkeypatch.setenv('LEAPP_HOSTNAME', _HOSTNAME)
    store_workflow_metadata(workflow)
    monkeypatch.delenv('LEAPP_EXECUTION_ID')
    monkeypatch.delenv('LEAPP_HOSTNAME')

    # ---
    # Test retrieve correct workflow metadata
    # ---
    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute(
            'SELECT * '
            'FROM entity '
            'JOIN metadata '
            'ON entity.metadata_hash = metadata.hash '
            'WHERE kind == "workflow" AND context = ? '
            'ORDER BY id DESC '
            'LIMIT 1;', (_CONTEXT_NAME,))
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['kind'] == 'workflow'
    assert entry['name'] == 'LeappDBUnitTest'
    assert entry['context'] == _CONTEXT_NAME

    metadata = json.loads(entry['metadata'])
    assert sorted(metadata.keys()) == sorted(_WORKFLOW_METADATA_FIELDS)
    assert metadata == _TEST_WORKFLOW_METADATA
