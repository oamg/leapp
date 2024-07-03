import os
import uuid

from leapp.utils.audit import get_connection, Execution
from leapp.utils.clicmd import command_aware_wraps


def last_snactor_context(connection=None):
    """
    Retrieves the last snactor-run context from the database. It generates a new one if none has been found.

    :param connection: Database connection to use instead of the default connection.
    :returns: String representing the latest snactor-run context uuid.
    """
    with get_connection(db=connection) as db:
        cursor = db.execute('''
            SELECT context, stamp FROM execution WHERE kind = 'snactor-run' ORDER BY id DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        if row:
            context = row[0]
        else:
            context = str(uuid.uuid4())
            Execution(context=context, kind='snactor-run', configuration='').store()
        return context


def with_snactor_context(f):
    @command_aware_wraps(f)
    def wrapper(*args, **kwargs):
        # To preserve context, one needs to LEAPP_DEBUG_PRESERVE_CONTEXT=1 and have LEAPP_EXECUTION_ID=<id> set.
        if not (os.environ.get('LEAPP_DEBUG_PRESERVE_CONTEXT', '0') == '1' and os.environ.get('LEAPP_EXECUTION_ID')):
            os.environ["LEAPP_EXECUTION_ID"] = last_snactor_context()
        return f(*args, **kwargs)
    return wrapper
