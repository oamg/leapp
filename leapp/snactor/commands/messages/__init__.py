from leapp.utils.clicmd import command
from leapp.utils.project import requires_project
from leapp.utils.audit import get_connection


@command('messages', help='Messaging related commands')
def messages(*args):
    pass


@messages.command('clear', help='Deletes all messages from the current scope')
@requires_project
def clear(args):
    get_connection(None).execute("""
      DELETE FROM message WHERE context IN (
        SELECT context FROM execution WHERE kind = 'snactor-run' ORDER BY stamp DESC LIMIT 1
      )
    """)
