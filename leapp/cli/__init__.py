import os
import socket

from leapp.utils.clicmd import command, command_opt
from leapp.cli import upgrade
from leapp import VERSION


@command('')
def cli(_):
    pass


def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    cli.command.add_sub(upgrade.list_runs.command)
    cli.command.add_sub(upgrade.preupgrade.command)
    cli.command.add_sub(upgrade.upgrade.command)
    cli.command.execute('leapp version {}'.format(VERSION))
