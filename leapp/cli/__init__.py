import os
import socket

from leapp.utils.clicmd import command, command_opt
import leapp.cli.upgrade
from leapp import VERSION


@command('')
@command_opt('debug', is_flag=True, help='Enable debug logging', inherit=True)
def cli(args):
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else os.environ.get('LEAPP_DEBUG', '0')


def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    cli.command.add_sub(leapp.cli.upgrade.upgrade.command)
    cli.command.execute('leapp version {}'.format(VERSION))
