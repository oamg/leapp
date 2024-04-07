import os
import pkgutil
import socket

from leapp.compat import load_module
from leapp.utils.i18n import _  # noqa; pylint: disable=redefined-builtin
from leapp.snactor import commands
from leapp.snactor.commands import workflow
from leapp.snactor.commands import messages
from leapp.snactor.commands import repo
from leapp.utils.clicmd import command, command_opt
from leapp.utils.repository import find_repository_basedir
from leapp import VERSION

SHORT_HELP = _("snactor is a development and repository management tool for Leapp.")
LONG_HELP = _("""Snactor is designed to get quickly started with leapp actor development.""")


def load_commands():
    _load_commands_from(commands.__file__)
    _load_commands_from(commands.workflow.__file__)
    _load_commands_from(commands.messages.__file__)
    _load_commands_from(commands.repo.__file__)
    cli.command.add_sub(messages.messages.command)
    cli.command.add_sub(workflow.workflow.command)
    cli.command.add_sub(repo.repo.command)


def _load_commands_from(path):
    pkg_path = os.path.dirname(path)
    for importer, name, is_pkg in pkgutil.iter_modules([pkg_path]):
        if is_pkg:
            continue
        mod = load_module(importer, name)
        if hasattr(mod.cli, 'command'):
            if not mod.cli.command.parent:
                cli.command.add_sub(mod.cli.command)


@command('', help=LONG_HELP)
@command_opt('debug', is_flag=True, help=_('Enables debug mode'), inherit=True)
@command_opt('verbose', is_flag=True, help=_('Enables verbose logging'), inherit=True)
@command_opt('config', help=_('Allows to override the leapp.conf location'), inherit=True)
@command_opt('logger-config', help=_('Allows to override the logger.conf location'), inherit=True)
def cli(args):
    if args.logger_config and os.path.isfile(args.logger_config):
        os.environ['LEAPP_LOGGER_CONFIG'] = args.logger_config
    # Consider using the in repository $REPOPATH/.leapp/logger.conf to actually obey --debug / --verbose
    # If /etc/leapp/logger.conf or $REPOPATH/.leapp/logger.conf don't exist logging won't work in snactor.
    elif find_repository_basedir('.') and os.path.isfile(os.path.join(find_repository_basedir('.'),
                                                                      '.leapp/logger.conf')):
        os.environ['LEAPP_LOGGER_CONFIG'] = os.path.join(find_repository_basedir('.'), '.leapp/logger.conf')

    config_file_path = None
    if args.config and os.path.isfile(args.config):
        config_file_path = args.config

    if not config_file_path and find_repository_basedir('.'):
        config_file_path = os.path.join(find_repository_basedir('.'), '.leapp/leapp.conf')

    if not config_file_path or not os.path.isfile(config_file_path):
        config_file_path = os.environ.get('LEAPP_CONFIG')

    if not config_file_path or not os.path.isfile(config_file_path):
        config_file_path = '/etc/leapp/leapp.conf'

    os.environ['LEAPP_CONFIG'] = config_file_path
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else os.environ.get('LEAPP_DEBUG', '0')

    if os.environ['LEAPP_DEBUG'] == '1' or args.verbose:
        os.environ['LEAPP_VERBOSE'] = '1'
    else:
        os.environ['LEAPP_VERBOSE'] = os.environ.get('LEAPP_VERBOSE', '0')


def main():
    os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
    load_commands()
    cli.command.execute(version=_('snactor version {}').format(VERSION))
