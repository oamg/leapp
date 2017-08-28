import os
import subprocess
from argparse import ArgumentParser
from pprint import pprint
from subprocess import PIPE

import argcomplete

from snactor import loader
from snactor import registry

ACTOR_DIRECTORY = '/usr/share/leapp/actors'
VERSION = "0.2-dev"


def _add_identity_options(cli_cmd, context=''):
    if context:
        cli_cmd.add_argument('--' + context + '-identity', default=None,
                             help='Path to private SSH key for the ' + context + ' machine')
        cli_cmd.add_argument('--' + context + '-user', default="root", help='Connect as this user to the ' + context)
    else:
        cli_cmd.add_argument('--identity', default=None, help='Path to private SSH key')
        cli_cmd.add_argument('--user', '-u', default="root", help='Connect as this user')


def _port_spec(arg):
    """Converts a port forwarding specifier to a (host_port, container_port) tuple

    Specifiers can be either a simple integer, where the host and container port are
    the same, or else a string in the form "host_port:container_port".
    """
    host_port, sep, container_port = arg.partition(":")
    host_port = int(host_port)
    if not sep:
        container_port = host_port
    else:
        container_port = int(container_port)
    return str(host_port), container_port


def _to_port_map(items):
    port_map = {}
    for source, target in items:
        port_map[source] = port_map.get(source, []) + [target]
    return {k: list(set(v)) for k, v in port_map.items()}


def _path_spec(arg):
    path = os.path.normpath(arg)
    if not os.path.isabs(path):
        raise ValueError("Path '{}' is not absolute or valid.".format(str(arg)))

    return path


def _make_argument_parser():
    ap = ArgumentParser()
    ap.add_argument('-v', '--version', action='version', version=VERSION, help='display version information')
    parser = ap.add_subparsers(help='sub-command', dest='action')
    migrate_cmd = parser.add_parser('migrate-machine', help='migrate source VM to a target container host')

    migrate_cmd.add_argument('machine', help='source machine to migrate')
    migrate_cmd.add_argument('-t', '--target', default='localhost', help='target VM name')
    migrate_cmd.add_argument(
        '--tcp-port',
        default=None,
        dest="forwarded_tcp_ports",
        nargs='*',
        type=_port_spec,
        help='(Re)define target tcp ports to forward to macrocontainer - [target_port:source_port]'
    )
    migrate_cmd.add_argument(
        '--no-tcp-port',
        default=None,
        dest="excluded_tcp_ports",
        nargs='*',
        type=_port_spec,
        help='define tcp ports which will be excluded from the mapped ports [[target_port]:source_port>]'
    )

    migrate_cmd.add_argument(
        '--exclude-path',
        default=None,
        dest="excluded_paths",
        nargs='*',
        type=_path_spec,
        help='define paths which will be excluded from the source'
    )
    migrate_cmd.add_argument("--ignore-default-port-map", default=False,
                             help='Default port mapping detected by leapp toll will be ignored', action="store_true")
    migrate_cmd.add_argument('--container-name', '-n', default=None,
                             help='Name of new container created on target host')
    migrate_cmd.add_argument(
        '--force-create',
        action='store_true',
        help='force creation of new target container, even if one already exists'
    )
    migrate_cmd.add_argument('--disable-start', dest='disable_start', default=False,
                             help='Migrated container will not be started immediately', action="store_true")
    _add_identity_options(migrate_cmd, context='source')
    _add_identity_options(migrate_cmd, context='target')

    return ap


def _make_base_object(s):
    return {"value": s}


def _start_agent_if_not_available():
    if 'SSH_AUTH_SOCK' in os.environ:
        return
    agent_details = subprocess.check_output(["ssh-agent", "-c"], stderr=PIPE).splitlines()
    agent_socket = agent_details[0].split()[2].rstrip(";")
    agent_pid = agent_details[1].split()[2].rstrip(";")
    os.environ["SSH_AUTH_SOCK"] = agent_socket
    os.environ["SSH_AGENT_PID"] = agent_pid


def _migrate_machine(arguments):
    loader.load(ACTOR_DIRECTORY)
    data = {
        "target_host": _make_base_object(arguments.target),
        "source_host": _make_base_object(arguments.machine),
        "tcp_port_list": {"tcp": _to_port_map(arguments.forwarded_tcp_ports)},
        "excluded_tcp_port_list": {"tcp": map(lambda x: int(x[0]), arguments.excluded_tcp_ports)},
        "excluded_paths": {"value": arguments.excluded_paths},
        "start_container": _make_base_object(not arguments.disable_start),
        "target_user_name": _make_base_object(arguments.target_user),
        "source_user_name": _make_base_object(arguments.source_user),
    }

    if not registry.get_actor('migrate-machine').execute(data):
        pprint(data)
        exit(-1)


def main():
    _COMMANDS = {
        'migrate-machine': _migrate_machine,
    }

    ap = _make_argument_parser()
    argcomplete.autocomplete(ap)
    parsed = ap.parse_args()

    for identity in ('identity', 'target_identity', 'source_identity'):
        if identity in parsed and getattr(parsed, identity):
            _start_agent_if_not_available()
            subprocess.call(['ssh-add', getattr(parsed, identity)])

    _COMMANDS[parsed.action](parsed)
