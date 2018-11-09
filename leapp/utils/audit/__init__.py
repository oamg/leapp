from contextlib import contextmanager
import datetime
import json
import os
import sqlite3

import six

from leapp.config import get_config
from leapp.utils.schemas import CURRENT_SCHEMA, MIGRATIONS


@contextmanager
def _umask(new_mask):
    cur_mask = os.umask(new_mask)
    yield
    os.umask(cur_mask)


def _initialize_database(db):
    """
    Checks that the latest schema of the database has been applied or initializes the database
    for new databases

    :param db: Connection object to the database
    :return: Pass through of the db object for convenience
    """
    schema_version = db.execute('PRAGMA schema_version').fetchone()[0]
    if not schema_version:
        db.executescript(CURRENT_SCHEMA)
    else:
        user_version = db.execute('PRAGMA user_version').fetchone()[0]
        versions = [m[0] for m in MIGRATIONS]
        try:
            index = versions.index(user_version)
        except ValueError:
            pass
        else:
            for migration in MIGRATIONS[index:]:
                db.executescript(migration[1])
    return db


def create_connection(path):
    """
    Creates a database connection to the path and ensures it's initialized and up to date.

    :param path: Path to the database
    :return: Connection object
    """
    with _umask(0o177):
        return _initialize_database(sqlite3.connect(path))


def get_connection(db):
    """
    Get the database connection or passes it through if it is already set

    :param db: Database connection to be passed through in case it exists already
    :return: database object initialized and migrated to the latest schema version
    """
    if db:
        return db
    cfg = get_config()
    return create_connection(cfg.get('database', 'path'))


class Storable(object):
    """
    Base class for database storables
    """

    def store(self, db=None):
        """
        Stores the data within a transaction
        :param db: Database object (optional)
        :return: None
        """
        with get_connection(db) as connection:
            self.do_store(connection)

    def do_store(self, connection):
        """
        Performs the actual storing of the data

        :param connection: Database connection to use (Can be a transaction cursor)
        :return: None
        """


class Execution(Storable):
    """
    Stores information about the current execution
    """

    @property
    def execution_id(self):
        """
        Returns the id of the entry, which is only set when already stored.
        :return: Integer id or None
        """
        return self._execution_id

    def __init__(self, context=None, kind=None, configuration=None, stamp=None):
        """
        :param context: Execution context identifier
        :type context: str
        :param kind: Execution kind - Can be any string and used for filtering
        :type kind: str
        :param configuration:
        :type configuration: str, dict, list or tuple
        :param stamp: Timestamp string of the execution start in iso format
        :type stamp: str
        """
        super(Execution, self).__init__()
        self.stamp = stamp or datetime.datetime.utcnow().isoformat() + 'Z'
        if not isinstance(configuration, str):
            configuration = json.dumps(configuration, sort_keys=True)
        self.configuration = configuration
        self.context = context
        self.kind = kind
        self._execution_id = None

    def do_store(self, connection):
        super(Execution, self).do_store(connection)
        connection.execute('INSERT OR IGNORE INTO execution (context, configuration, stamp, kind) VALUES(?, ?, ?, ?)',
                           (self.context, self.configuration, self.stamp, self.kind))
        cursor = connection.execute('SELECT id FROM execution WHERE context = ?',
                                    (self.context,))
        self._execution_id = cursor.fetchone()[0]


class Host(Storable):
    """
    Host information
    """
    def __init__(self, context=None, hostname=None):
        self.context = context
        self.hostname = hostname
        self._host_id = None

    @property
    def host_id(self):
        """
        Returns the id of the entry, which is only set when already stored.
        :return: Integer id or None
        """
        return self._host_id

    def do_store(self, connection):
        super(Host, self).do_store(connection)
        connection.execute('INSERT OR IGNORE INTO host (context, hostname) VALUES(?, ?)',
                           (self.context, self.hostname))
        cursor = connection.execute('SELECT id FROM host WHERE context = ? AND hostname = ?',
                                    (self.context, self.hostname))
        self._host_id = cursor.fetchone()[0]


class MessageData(Storable):
    """
    Message data
    """
    def __init__(self, data=None, hash_id=None):
        """
        :param data: Message payload
        :type data: str
        :param hash_id: SHA256 hash in hexadecimal representation of data
        :type hash_id: str
        """
        super(MessageData, self).__init__()
        self.data = data
        self.hash_id = hash_id

    def do_store(self, connection):
        super(MessageData, self).do_store(connection)
        connection.execute('INSERT OR IGNORE INTO message_data (hash, data) VALUES(?, ?)', (self.hash_id, self.data))


class DataSource(Host):
    def __init__(self, actor=None, phase=None, context=None, hostname=None):
        """
        :param actor: Name of the actor that triggered the entry
        :type actor: str
        :param phase: In which phase of the workflow execution the data entry was created
        :type phase: str
        :param context: The execution context
        :type context: str
        :param hostname: Hostname of the system that produced the entry
        :type hostname: str
        """
        super(DataSource, self).__init__(context=context, hostname=hostname)
        self.actor = actor
        self.phase = phase
        self._data_source_id = None

    @property
    def data_source_id(self):
        """
        Returns the id of the entry, which is only set when already stored.
        :return: Integer id or None
        """
        return self._data_source_id

    def do_store(self, connection):
        super(DataSource, self).do_store(connection)
        connection.execute('INSERT OR IGNORE INTO data_source (context, host_id, actor, phase) VALUES(?, ?, ?, ?)',
                           (self.context, self.host_id, self.actor, self.phase))
        cursor = connection.execute(
            'SELECT id FROM data_source WHERE context = ? AND host_id = ? AND actor = ? AND phase = ?',
            (self.context, self.host_id, self.actor, self.phase))
        self._data_source_id = cursor.fetchone()[0]


class Message(DataSource):
    def __init__(self, stamp=None, msg_type=None, topic=None, data=None, actor=None, phase=None,
                 hostname=None, context=None):
        """
        :param stamp: Timestamp string of the message creation in iso format
        :type stamp: str
        :param msg_type: Name of the model that represents the message payload
        :type msg_type: str
        :param topic: Topic for this message
        :type topic: str
        :param data: Payload data
        :type data: :py:class:`leapp.utils.audit.MessageData`
        :param actor: Name of the actor that triggered the entry
        :type actor: str
        :param phase: In which phase of the workflow execution the message was created
        :type phase: str
        :param context: The execution context
        :type context: str
        :param hostname: Hostname of the system that produced the message
        :type hostname: str
        """
        super(Message, self).__init__(actor=actor, phase=phase, hostname=hostname, context=context)
        self.stamp = stamp or datetime.datetime.utcnow().isoformat() + 'Z'
        self.msg_type = msg_type
        self.topic = topic
        self.data = data
        self._message_id = None

    @property
    def message_id(self):
        """
        Returns the id of the entry, which is only set when already stored.
        :return: Integer id or None
        """
        return self._message_id

    def do_store(self, connection):
        super(Message, self).do_store(connection)
        self.data.do_store(connection)
        cursor = connection.execute(
            'INSERT INTO message (context, stamp, topic, type, data_source_id, message_data_hash) '
            'VALUES(?, ?, ?, ?, ?, ?)',
            (self.context, self.stamp, self.topic, self.msg_type, self.data_source_id, self.data.hash_id))
        self._message_id = cursor.lastrowid


class Audit(DataSource):
    def __init__(self, event=None, stamp=None, message=None, data=None, actor=None, phase=None, hostname=None,
                 context=None):
        """
        :param event: Type of this event e.g. new-message or log-message but can be anything
        :type event: str
        :param stamp: Timestamp string of the event creation in iso format
        :type stamp: str
        :param message: A message object, if this audit entry represents a message otherwise None
        :type message: :py:class:`leapp.utils.audit.Message` or None
        :param data: If message is None this has to be the data for the audit entry
        :type data: str or None
        :param actor: Name of the actor that triggered the entry
        :type actor: str
        :param phase: In which phase of the workflow execution the data entry was created
        :type phase: str
        :param context: The execution context
        :type context: str
        :param hostname: Hostname of the system that produced the entry
        :type hostname: str
        """
        super(Audit, self).__init__(actor=actor, phase=phase, hostname=hostname, context=context)
        self.event = event
        self.stamp = stamp or datetime.datetime.utcnow().isoformat() + 'Z'
        self.message = message
        self.data = data
        self._audit_id = None

    @property
    def audit_id(self):
        return self._audit_id

    def do_store(self, connection):
        if self._audit_id:
            return

        super(Audit, self).do_store(connection)

        if self.message and not self.message.message_id:
            self.message.do_store(connection)

        if self.data and not isinstance(self.data, six.string_types):
            self.data = json.dumps(self.data)

        cursor = connection.execute(
            'INSERT INTO audit (event, stamp, context, data_source_id, message_id, data)'
            ' VALUES(?, ?, ?, ?, ?, ?)',
            (self.event, self.stamp, self.context, self.data_source_id,
             self.message.message_id if self.message else None, self.data))

        self._audit_id = cursor.lastrowid


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


_MESSAGE_QUERY_TEMPLATE = '''
        SELECT
             id, context, stamp, topic, type, actor, phase, message_hash, message_data, hostname
        FROM
             messages_data
        WHERE context = ? AND type IN (%s)'''


def get_messages(names, context):
    """
    Queries all messages from the database for the given context and the list of model names
    :param names: List of names that should be messages returned for
    :type names: list or tuple of str
    :param context: Execution id the message should be queried from.
    :return: Iterable with messages
    :rtype: iterable
    """
    if not names:
        return ()

    with get_connection(None) as conn:
        cursor = conn.execute(_MESSAGE_QUERY_TEMPLATE % ', '.join('?' * len(names)), (context,) + tuple(names))
        cursor.row_factory = _dict_factory
        result = cursor.fetchall()

        # Transform to expected format
        for row in result:
            row['message'] = {'data': row.pop('message_data'), 'hash': row.pop('message_hash')}
        return result


_AUDIT_CHECKPOINT_EVENT = 'checkpoint'


def checkpoint(actor, phase, context, hostname):
    """
    Creates a checkpoint audit entry

    :param actor: Name of the actor that triggered the entry
    :type actor: str
    :param phase: In which phase of the workflow execution the data entry was created
    :type phase: str
    :param context: The execution context
    :type context: str
    :param hostname: Hostname of the system that produced the entry
    :type hostname: str
    :return: None
    """

    audit = Audit(event=_AUDIT_CHECKPOINT_EVENT, actor=actor, phase=phase, hostname=hostname, context=context)
    audit.store()


def get_errors(context):
    """
    Queries all error messages from the database for the given context

    :param context: The execution context
    :type context: str
    :return: List of error messages
    """
    return get_messages(('ErrorModel',), context=context)


def get_checkpoints(context):
    """
    Retrieve all checkpoints stored in the database for the given context

    :param context: The execution context
    :type context: str
    :return: list of dicts with id, timestamp, actor and phase fields
    """
    with get_connection(None) as conn:
        cursor = conn.execute('''
            SELECT
                audit.id          AS id,
                audit.stamp       AS stamp,
                data_source.actor AS actor,
                data_source.phase AS phase
              FROM
                audit
              JOIN
                data_source ON data_source.id = audit.data_source_id
              WHERE
                audit.context = ? AND audit.event = ?
              ORDER BY stamp ASC;
        ''', (context, _AUDIT_CHECKPOINT_EVENT))
        cursor.row_factory = _dict_factory
        return cursor.fetchall()
