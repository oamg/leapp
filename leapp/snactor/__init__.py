import os
import pkgutil
import socket

from leapp.snactor import commands
from leapp.snactor.commands import workflow
from leapp.snactor.commands import messages
from leapp.utils.clicmd import command, command_opt, execute_command
from leapp.utils.project import find_project_basedir
from leapp import VERSION

SHORT_HELP = "actor-snactor is a leapp actor project management snactor"
LONG_HELP = """
This snactor is designed to get quickly started with leapp actor development
"""


def load_commands():
    _load_commands_from(commands.__file__)
    _load_commands_from(commands.workflow.__file__)
    _load_commands_from(commands.messages.__file__)
    cli.command.add_sub(messages.messages.command)
    cli.command.add_sub(workflow.workflow.command)


def _load_commands_from(path):
    pkg_path = os.path.dirname(path)
    for importer, name, is_pkg in pkgutil.iter_modules([pkg_path]):
        if is_pkg:
            continue
        mod = importer.find_module(name).load_module(name)
        if hasattr(mod.cli, 'command'):
            if not mod.cli.command.parent:
                cli.command.add_sub(mod.cli.command)


@command('', help=LONG_HELP)
@command_opt('debug', is_flag=True, help='Enables debug logging', inherit=True)
@command_opt('config', help='Allows to override the leapp.conf location', inherit=True)
@command_opt('logger-config', help='Allows to override the logger.conf location', inherit=True)
def cli(args):
    if args.logger_config and os.path.isfile(args.logger_config):
        os.environ['LEAPP_LOGGER_CONFIG'] = args.logger_config

    config_file_path = None
    if args.config and os.path.isfile(args.config):
        config_file_path = args.config

    if not config_file_path and find_project_basedir('.'):
        config_file_path = os.path.join(find_project_basedir('.'), '.leapp/leapp.conf')

    if not config_file_path or not os.path.isfile(config_file_path):
        config_file_path = os.environ.get('LEAPP_CONFIG')

    if not config_file_path or not os.path.isfile(config_file_path):
        config_file_path = '/etc/leapp/leapp.conf'

    os.environ['LEAPP_CONFIG'] = config_file_path
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else '0'


def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    load_commands()
    cli.command.execute(version='snactor version {}'.format(VERSION))
