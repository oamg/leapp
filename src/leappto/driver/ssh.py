import getpass
import json
import os
import shlex
import socket

try:
    from pipes import quote
except ImportError:
    from shelx import quote


import paramiko

from leappto.driver import Driver, LocalDriver


class SSHError(Exception):
    pass


class SSHConnectionError(SSHError):
    pass


class SSHHostKeyError(SSHError):
    pass


class SSHAuthenticationError(SSHError):
    pass


class ParamikoConnection(object):
    def __init__(self, hostname, username=None, port=22, strict_host_key=True):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.connect((hostname, port))
        except socket.error as e:
            raise SSHConnectionError('Failed to connect to {}:{} ERROR: {}'.format(hostname, port, e.message))
        self._transport = paramiko.Transport(self._socket)

        try:
            self._transport.start_client()
        except paramiko.SSHException:
            raise SSHConnectionError('SSH negotiation failed while connecting to: {}:{}'.format(hostname, port))

        try:
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            host_keys = paramiko.hostkeys.HostKeys()

        if strict_host_key:
            remote_key = self._transport.get_remote_server_key()
            if not host_keys.check(hostname, remote_key):
                raise SSHHostKeyError(
                        'Could not find {} - {} in known hosts for host {}'.format(
                            remote_key.get_name(),
                            remote_key.get_base64(),
                            hostname))
            else:
                pass #  OK

        self.username = username or getpass.getuser()
        agent_keys = paramiko.Agent().get_keys()
        for key in agent_keys:
            try:
                self._transport.auth_publickey(self.username, key)
                break
            except paramiko.SSHException:
                pass
        if not self._transport.is_authenticated():
            raise SSHAuthenticationError('Could not find auth key for {}@{}'.format(self.username, hostname))


    def exec_command(self, cmd, *args, **kwargs):
        chan = self._transport.open_session()
        chan.exec_command(cmd)
        stdin = chan.makefile('wb', 1)
        stdout = chan.makefile('r', 1)
        stderr = chan.makefile_stderr('r', 1)
        return stdin, stdout, stderr


class SSHConfig(object):
    def __init__(self, hostname, username=None, port=22, strict_host_key_checking=False, identity_file=None,
                 use_pass=False, control_path=None, options=None):
        self._options = options or {}
        self._add_opt('User', username)
        self._add_opt('IdentityFile', username)
        self._add_opt('Host', hostname)
        self._add_opt('Port', port, int)
        self._add_opt('PasswordAuthentication', 'yes' if use_pass else 'no')
        self._add_opt('StrictHostKeyChecking', 'yes' if strict_host_key_checking else 'no')
        self._add_opt('ControlPath', control_path)

    def ssh_cmd(self, *args, **kwargs):
        options = self._options.copy()
        options.update(kwargs)
        return ['ssh'] + [e for l in [['-v', '{}={}'.format(k, v)] for k, v in options.items] for e in l] + list(args)

    def _add_opt(self, name, value, value_type=basestring):
        if value:
            if not value_type or isinstance(value, value_type):
                self._options[name] = value
            else:
                raise TypeError('{} should be of type {}'.format(name, value_type.__name__))


class SSHConnection(LocalDriver):
    def __init__(self, config):
        self._config = config
        super(LocalDriver, self).__init__()
    def exec_command(self, cmd, *args, **kwargs):
        return super(SSHConnection, self).exec_command('ssh ' +  self._target + ' ' + quote(cmd), *args)


class VagrantSSHDriver(Driver):
    def __init__(self, domain_name):
        self._connection = VagrantSSHDriver._get_vagrant_ssh_client_for_domain(domain_name)

    def exec_command(self, *args, **kwargs):
        return self._connection.exec_command(*args, **kwargs)

    @staticmethod
    def _get_vagrant_data_path_from_domain(domain_name):
        index_path = os.path.join(os.environ['HOME'], '.vagrant.d/data/machine-index/index')
        index = json.load(open(index_path, 'r'))
        for ident, machine in index['machines'].iteritems():
            path_name = os.path.basename(machine['vagrantfile_path'])
            vagrant_name = machine.get('name', 'default')
            if domain_name == path_name + '_' + vagrant_name:
                return machine['local_data_path']
        return None

    @staticmethod
    def _get_vagrant_ssh_args_from_domain(domain_name):
        path = VagrantSSHDriver._get_vagrant_data_path_from_domain(domain_name)
        path = os.path.join(path, 'provisioners/ansible/inventory/vagrant_ansible_inventory')
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line[0] in (';', '#'):
                    continue
                return VagrantSSHDriver._parse_ansible_inventory_data(line)
        return None

    @staticmethod
    def _parse_ansible_inventory_data(line):
        parts = shlex.split(line)
        if parts:
            parts = parts[1:]
        args = {}
        mapping = {
                'ansible_ssh_port': ('port', int),
                'ansible_ssh_host': ('hostname', str),
                'ansible_ssh_private_key_file': ('key_filename', str),
                'ansible_ssh_user': ('username', str)}
        for part in parts:
            key, value = part.split('=', 1)
            if key in mapping:
                args[mapping[key][0]] = mapping[key][1](value)
        return args

    @staticmethod
    def _get_vagrant_ssh_client_for_domain(domain_name):
        args = VagrantSSHDriver._get_vagrant_ssh_args_from_domain(domain_name)
        if args:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(args.pop('hostname'), **args)
            return client
        return None


class SSHDriver(Driver):
    def __init__(self, hostname, username=None, port=22, use_paramiko=True):
        super(SSHDriver, self).__init__()
        if use_paramiko:
            self._connection = ParamikoConnection(hostname, username=username, port=port)
        else:
            self._connection = SSHConnection(hostname, username=username, port=port)

    def exec_command(self, *args, **kwargs):
        return self._connection.exec_command(*args, **kwargs)
