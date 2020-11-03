import os
import socket
# profiling
import cProfile
import pstats
import six

from leapp.utils.clicmd import command, command_opt
from leapp.cli import upgrade
from leapp import VERSION


@command('')
def cli(args): # noqa; pylint: disable=unused-argument
    pass


def main():
    os.environ['LEAPP_CPROFILE'] = os.environ.get('LEAPP_CPROFILE', '0')
    profile_enabled = os.environ['LEAPP_CPROFILE'] == '1'
    if profile_enabled:
        pr = cProfile.Profile()
        pr.enable()
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    for cmd in [upgrade.list_runs, upgrade.preupgrade, upgrade.upgrade, upgrade.answer]:
        cli.command.add_sub(cmd.command)
    cli.command.execute('leapp version {}'.format(VERSION))
    if profile_enabled:
        pr.disable()
        s = six.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
