
import os
import pkgutil
import socket

from leapp import VERSION
from leapp.cli import commands
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
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    _load_commands(cli.command)
    cli.command.execute('leapp version {}'.format(VERSION))
