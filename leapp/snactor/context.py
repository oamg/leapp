import os
import uuid

from leapp.utils.audit import get_connection, Execution
from leapp.utils.clicmd import command_aware_wraps


def with_snactor_context(f):
    @command_aware_wraps(f)
    def wrapper(*args, **kwargs):
        with get_connection(None) as db:
            cursor = db.execute("""
              SELECT context, stamp FROM execution WHERE kind = 'snactor-run' ORDER BY stamp DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                context = row[0]
            else:
                context = str(uuid.uuid4())
                Execution(context=str(uuid.uuid4()), kind='snactor-run', configuration='').store()
            os.environ["LEAPP_EXECUTION_ID"] = context
        return f(*args, **kwargs)
    return wrapper
