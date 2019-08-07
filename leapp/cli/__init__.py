import os
import socket

from leapp.utils.clicmd import command, command_opt
from leapp.cli import upgrade
from leapp import VERSION


@command('')
@command_opt('debug', is_flag=True, help='Enable debug mode', inherit=True)
@command_opt('verbose', is_flag=True, help='Enable verbose logging', inherit=True)
def cli(args):
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else os.environ.get('LEAPP_DEBUG', '0')
    if os.environ['LEAPP_DEBUG'] == '1' or args.verbose:
        os.environ['LEAPP_VERBOSE'] = '1'
    else:
        os.environ['LEAPP_VERBOSE'] = os.environ.get('LEAPP_VERBOSE', '0')


def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    cli.command.add_sub(upgrade.list_runs.command)
    cli.command.add_sub(upgrade.preupgrade.command)
    cli.command.add_sub(upgrade.upgrade.command)
    cli.command.execute('leapp version {}'.format(VERSION))
