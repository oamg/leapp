import os

from leapp.utils.clicmd import command
from leapp.utils.project import requires_project
from leapp.snactor.context import with_snactor_context
from leapp.utils.audit import get_connection, get_config

_MAIN_LONG_DESCRIPTION = '''
This group of commands are around managing messages stored in the
current project database.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@command('messages', help='Messaging related commands', description=_MAIN_LONG_DESCRIPTION)
def messages(args):
    pass


_CLEAR_LONG_DESCRIPTION = '''
With this command messages in the current project scope can be wiped.
This gives the developer control over the input data available to actors
run and developed in this project.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@messages.command('clear', help='Deletes all messages from the current project scope',
                  description=_CLEAR_LONG_DESCRIPTION)
@requires_project
@with_snactor_context
def clear(args):
    print("Deleting all messages with context = {} in database {}".format(
        os.environ["LEAPP_EXECUTION_ID"],
        get_config().get("database", "path")
    ))
    with get_connection(None) as con:
        con.execute("DELETE FROM message WHERE context = ?", (os.environ["LEAPP_EXECUTION_ID"],))
