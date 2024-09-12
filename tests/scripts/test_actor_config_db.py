import os
import hashlib
import json

from leapp.utils.audit import (get_connection, dict_factory, ActorConfigData, ActorConfig)
from leapp.config import get_config

_CONTEXT_NAME = 'test-context-name-actor-config-db'
_TEST_ACTOR_CONFIG = {}


def setup_module():
    get_config().set('database', 'path', '/tmp/leapp-test.db')


def setup():
    path = get_config().get('database', 'path')
    if os.path.isfile(path):
        os.unlink(path)


def test_save_empty_actor_config_data():
    hash_id = hashlib.sha256('test-empty-actor-config'.encode('utf-8')).hexdigest()
    cfg = ActorConfigData(hash_id=hash_id, config='')
    cfg.store()

    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute('SELECT * FROM actor_config_data WHERE hash = ?;', (hash_id,))
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['config'] == ''


def test_save_empty_actor_config():
    hash_id = hashlib.sha256('test-empty-actor-config'.encode('utf-8')).hexdigest()
    acd = ActorConfigData(hash_id=hash_id, config='')
    ac = ActorConfig(
        context=_CONTEXT_NAME,
        config=acd,
    )
    ac.store()

    assert ac.actor_config_id

    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute('SELECT * FROM actor_config WHERE id = ?;', (ac.actor_config_id,))
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['context'] == _CONTEXT_NAME
    assert entry['actor_config_hash'] == hash_id


def test_store_actor_config():
    hash_id = hashlib.sha256('test-actor-config'.encode('utf-8')).hexdigest()
    config_str = json.dumps(_TEST_ACTOR_CONFIG, sort_keys=True)
    acd = ActorConfigData(hash_id=hash_id, config=config_str)
    ac = ActorConfig(
        context=_CONTEXT_NAME,
        config=acd,
    )
    ac.store()

    assert ac.actor_config_id

    entry = None
    with get_connection(None) as conn:
        cursor = conn.execute(
            'SELECT * FROM actor_config WHERE id = ?;', (ac.actor_config_id,))
        cursor = conn.execute(
            'SELECT * '
            'FROM actor_config '
            'JOIN actor_config_data '
            'ON actor_config.actor_config_hash = actor_config_data.hash '
            'WHERE actor_config.id = ?;',
            (ac.actor_config_id,)
        )
        cursor.row_factory = dict_factory
        entry = cursor.fetchone()

    assert entry is not None
    assert entry['context'] == _CONTEXT_NAME
    assert entry['actor_config_hash'] == hash_id
    ans_config = json.loads(entry['config'])
    assert ans_config == {}
