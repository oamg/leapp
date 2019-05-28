"""
This module is currently single workflow specific (upgrades). After introducing other use cases we can make it
more robust
"""

from __future__ import print_function
import os
import sys

from leapp.exceptions import CommandError
from leapp.utils.clicmd import command, command_opt, command_arg
from leapp.utils.report import fetch_upgrade_report_messages
from leapp.cli.upgrade import fetch_last_upgrade_context


@command('report', help='Create report for last upgrade execution (default) or specific execution id')
@command_opt('id', help='ID of particular run to print report for. See # leapp list-runs for a list of all runs')
@command_opt('format', help='Format report using particular renderers. By default: "plaintext"')
def report(args):
    if os.getuid():
        raise CommandError('This command has to be run under the root user.')

    upgrade_id = args.id or fetch_last_upgrade_context()[0]

    if not upgrade_id:
        raise CommandError(
            'No previous Leapp upgrade run found. This command can only be run after "leapp upgrade" has been executed'
        )

    # FIXME: add proper default and choices parameters for the format option
    if args.format not in ('html', 'plaintext'):
        print('No / not supported renderer provided as --format (available renderers: "html", "plaintext"). '
              'Defaulting to "plaintext"', file=sys.stdout, end='\n\n')
        renderer = 'plaintext'
    else:
        renderer = args.format

    messages = fetch_upgrade_report_messages(upgrade_id, renderer)
    if not messages:
        raise CommandError('No upgrade report messages found for context {}'.format(upgrade_id))

    print(messages, file=sys.stdout)
