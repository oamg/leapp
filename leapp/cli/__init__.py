import os
import socket

from leapp.utils.clicmd import command, command_opt
from leapp.cli import upgrade
from leapp import VERSION


@command('')
def cli(args): # noqa; pylint: disable=unused-argument
    pass


def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    for cmd in [upgrade.list_runs, upgrade.preupgrade, upgrade.upgrade, upgrade.answer, upgrade.rerun]:
        cli.command.add_sub(cmd.command)
    cli.command.execute('leapp version {}'.format(VERSION))
