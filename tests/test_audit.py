import json
import os
import sqlite3

from leapp.utils.audit import get_connection, Execution, Host, MessageData, \
    DataSource, Message, Audit, get_messages, checkpoint, get_checkpoints
from leapp.config import get_config

_HOSTNAME = 'test-host.example.com'
_CONTEXT_NAME = 'test-context-name'
_ACTOR_NAME = 'test-actor-name'
_PHASE_NAME = 'test-phase-name'
_MESSAGE_TYPE = 'MessageType'
_TOPIC_NAME = 'test-topic'

_ORIGINAL_DB_SCHEMA = '''
CREATE TABLE execution (
  id            INTEGER PRIMARY KEY NOT NULL,
  context       VARCHAR(36)         NOT NULL UNIQUE,
  stamp         TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  configuration TEXT                         DEFAULT NULL
);

CREATE TABLE host (
  id       INTEGER PRIMARY KEY NOT NULL,
  context  VARCHAR(36)         NOT NULL REFERENCES execution (context),
  hostname VARCHAR(255)        NOT NULL,
  UNIQUE (context, hostname)
);

CREATE TABLE message_data (
  hash VARCHAR(64) PRIMARY KEY NOT NULL,
  data TEXT
);

CREATE TABLE data_source (
  id      INTEGER PRIMARY KEY NOT NULL,
  context VARCHAR(36)         NOT NULL REFERENCES execution (context),
  host_id INTEGER             NOT NULL REFERENCES host (id),
  actor   VARCHAR(1024)       NOT NULL DEFAULT '',
  phase   VARCHAR(1024)       NOT NULL DEFAULT '',
  UNIQUE (context, host_id, actor, phase)
);


CREATE TABLE message (
  id                INTEGER PRIMARY KEY NOT NULL,
  context           VARCHAR(36)         NOT NULL REFERENCES execution (context),
  stamp             TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  channel           VARCHAR(1024)       NOT NULL,
  type              VARCHAR(1024)       NOT NULL,
  data_source_id    INTEGER             NOT NULL REFERENCES data_source (id),
  message_data_hash VARCHAR(64)         NOT NULL REFERENCES message_data (hash)
);


CREATE TABLE audit (
  id             INTEGER PRIMARY KEY NOT NULL,
  event          VARCHAR(256)        NOT NULL REFERENCES execution (context),
  stamp          TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  context        VARCHAR(36)         NOT NULL,
  data_source_id INTEGER             NOT NULL REFERENCES data_source (id),

  message_id     INTEGER                      DEFAULT NULL REFERENCES message (id),
  data           TEXT                         DEFAULT NULL
);


CREATE VIEW messages_data AS
  SELECT
    message.id        AS id,
    message.context   AS context,
    message.stamp     AS stamp,
    message.channel   AS channel,
    message.type      as type,
    data_source.actor as actor,
    data_source.phase as phase,
    msg_data.hash     as message_hash,
    msg_data.data     as message_data,
    host.hostname     as hostname
  FROM
    message
    JOIN
    data_source ON data_source.id = message.data_source_id
    ,
    message_data as msg_data ON message.message_data_hash = msg_data.hash,
  host ON host.id = data_source.host_id;
'''


def setup_module(m):
    get_config().set('database', 'path', '/tmp/leapp-test.db')


def setup():
    path = get_config().get('database', 'path')
    if os.path.isfile(path):
        os.unlink(path)


def test_migrations_are_applied():
    con = sqlite3.connect(get_config().get('database', 'path'))
    con.executescript(_ORIGINAL_DB_SCHEMA)
    assert con.execute("PRAGMA user_version").fetchone()[0] == 0
    con.close()

    db = get_connection(None)
    assert db.execute("PRAGMA user_version").fetchone()[0] > 0


def test_pass_through():
    db = get_connection(None)
    db2 = get_connection(db)
    assert db is db2


def test_execution():
    e = Execution(context=_CONTEXT_NAME, configuration=json.dumps({'data': 'nothing to store'}))
    e.store()
    assert e.execution_id


def test_host():
    e = Host(context=_CONTEXT_NAME, hostname=_HOSTNAME)
    e.store()
    assert e.host_id


def test_message_data(saved=True):
    e = MessageData(data='abc', hash_id='abc')
    if saved:
        e.store()
        data = get_connection(None).execute(
            'SELECT data from message_data WHERE hash = "abc"').fetchone()[0]
        assert data == 'abc'
    return e


def test_data_source():
    e = DataSource(actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME, hostname=_HOSTNAME)
    e.store()
    assert e.data_source_id
    assert e.host_id
    return e


def test_message(saved=True):
    data = test_message_data(saved=True)
    e = Message(actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME, hostname=_HOSTNAME,
                topic=_TOPIC_NAME, msg_type=_MESSAGE_TYPE, data=data)
    if saved:
        e.store()
        assert e.message_id
        assert e.host_id
        assert e.data_source_id
    return e


def test_message_not_saved_data():
    data = test_message_data(saved=False)
    e = Message(actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME, hostname=_HOSTNAME,
                topic=_TOPIC_NAME, msg_type=_MESSAGE_TYPE, data=data)
    e.store()
    assert e.message_id
    assert e.host_id
    assert e.data_source_id


def test_audit_message():
    msg = test_message(saved=True)
    e = Audit(event='new-message', message=msg, actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME,
              hostname=_HOSTNAME)
    e.store()
    assert e.data_source_id
    assert e.host_id
    assert e.message.message_id
    assert e.message.data_source_id == e.data_source_id
    assert e.message.host_id == e.host_id


def test_audit_not_saved_message():
    msg = test_message(saved=False)
    e = Audit(event='new-message', message=msg, actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME,
              hostname=_HOSTNAME)
    e.store()
    assert e.data_source_id
    assert e.host_id
    assert e.message.message_id
    assert e.message.data_source_id == e.data_source_id
    assert e.message.host_id == e.host_id


def test_audit_data():
    e = Audit(event='new-message', data='Some data', actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME,
              hostname=_HOSTNAME)
    e.store()
    assert e.data_source_id
    assert e.host_id
    assert not e.message


def test_audit_non_string_data():
    e = Audit(event='new-message', data=['Some data'], actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME,
              hostname=_HOSTNAME)
    e.store()
    assert e.data_source_id
    assert e.host_id
    assert not e.message


def test_get_messages():
    assert not get_messages((), _CONTEXT_NAME)
    messages = get_messages((_MESSAGE_TYPE,), _CONTEXT_NAME)
    assert messages is not None and len(messages) == 0

    test_message()
    messages = get_messages((_MESSAGE_TYPE,), _CONTEXT_NAME)
    assert messages and len(messages) == 1


def test_checkpoints():
    checkpoint(actor=_ACTOR_NAME, phase=_PHASE_NAME, context=_CONTEXT_NAME, hostname=_HOSTNAME)
    result = get_checkpoints(_CONTEXT_NAME)
    assert result and len(result) == 1
    assert result[0]['id']
    assert result[0]['actor'] == _ACTOR_NAME
    assert result[0]['phase'] == _PHASE_NAME
    assert result[0]['stamp'].endswith('Z')
