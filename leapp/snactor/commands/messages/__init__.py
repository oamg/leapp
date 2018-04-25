import os

from leapp.utils.clicmd import command
from leapp.utils.project import requires_project
from leapp.snactor.context import with_snactor_context
from leapp.utils.audit import get_connection, get_config


@command('messages', help='Messaging related commands')
def messages(*args):
    pass


@messages.command('clear', help='Deletes all messages from the current project scope')
@requires_project
@with_snactor_context
def clear(args):
    print("Deleting all messages with context = {} in database {}".format(
        os.environ["LEAPP_EXECUTION_ID"],
        get_config().get("database", "path")
    ))
    with get_connection(None) as con:
        con.execute("DELETE FROM message WHERE context = ?", (os.environ["LEAPP_EXECUTION_ID"],))
