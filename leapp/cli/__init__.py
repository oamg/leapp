import os
import pkgutil
import socket
import sys
import textwrap

from leapp import VERSION
from leapp.cli import commands
from leapp.exceptions import UnknownCommandError
from leapp.utils.clicmd import command


@command('')
def cli(args):  # noqa; pylint: disable=unused-argument
    """
    Top level base command dummy function
    """


def _load_commands(base_command):
    pkgdir = os.path.dirname(commands.__file__)
    for entry in os.listdir(pkgdir):
        entry_path = os.path.join(pkgdir, entry)
        if os.path.isdir(entry_path) and os.path.isfile(os.path.join(entry_path, '__init__.py')):
            # We found a package - We will import it and get the `register` symbol and check if it is callable.
            package_name = 'leapp.cli.commands.{}'.format(entry)
            package = pkgutil.get_loader(package_name).load_module(package_name)
            register = getattr(package, 'register', None)
            if callable(register):
                register(base_command)


def main():
    """
    leapp entry point
    """

    if os.getuid() != 0:
        sys.stderr.write('Leapp has to be executed with root privileges.\n')
        sys.exit(1)

    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    _load_commands(cli.command)
    try:
        cli.command.execute('leapp version {}'.format(VERSION))
    except UnknownCommandError as e:
        print(textwrap.dedent('''
        Command "{CMD}" is unknown.
        Most likely there is a typo in the command or particular leapp repositories that provide this command
        are not present on the system.
        You can try to install the missing content e.g. by the following command: `dnf install 'leapp-command({CMD})'`
        '''.format(CMD=e.requested)))
        sys.exit(1)
