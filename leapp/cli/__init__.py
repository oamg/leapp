import argparse
import os

from leapp.utils.clicmd import command, command_opt
import leapp.cli.upgrade
from leapp import VERSION

@command('')
@command_opt('debug', is_flag=True, help='Enable debug logging', inherit=True)
def cli(args):
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else '0'


def main():
    cli.command.add_sub(leapp.cli.upgrade.upgrade.command)
    parser = argparse.ArgumentParser(prog='leapp')
    parser.add_argument('--version', action='version', version='leapp version {}'.format(VERSION))
    parser.set_defaults(func=None)
    s = parser.add_subparsers(description='Main commands')
    cli.command.apply_parser(s, parser=parser)
    args = parser.parse_args()
    args.func(args)
