import getpass
import os
import socket

import paramiko

from leappto.driver import Driver, LocalDriver


class SSHConnectionError(Exception):
    pass


class SSHHostKeyError(Exception):
    pass



class ParamikoConnection(object):
    def __init__(self, hostname, username=None, port=22, strict_host_key=True):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.connect((hostname, port))
        except socket.error as e:
            raise SSHConnectionError('Failed to connect to {}:{}: {}'.format(hostname, port, e.message))
        self._transport = paramiki.Transport(self._socket)

        try:
            self._transport.start_client()
        except paramiko.SSHException:
            raise SSHConnectionError('SSH negotiation failed while connecting to: {}:{}'.format(hostname, port))

        try:
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            host_keys = {}

        if strict_host_key:
            remote_key = self._transport.get_remote_server_key()
            if hostname not in host_keys:
                raise SSHHostKeyError('Could not find {} in known hosts'.format(hostname))
            elif remote_key.get_name() not in host_keys[hostname]:
                raise SSHHostKeyError('Key {} for host {} is unknown'.format(remote_key.get_name(), hostname))
            elif host_keys[hostname][remote_key.get_name()] != remote_key:
                raise SSHHostKeyError('Key for host {} has changed!'.format(hostname))
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

        self._session = self._transport.open_session()

    def exec_command(self, *args, **kwargs):
        return self._session.exec_command(*args, **kwargs)


class SSHConnection(LocalDriver):
    def __init__(self, hostname, username=None, port=22):
        userspec = username + '@' if username else ''
        self._target = '{}{}:{}'.format(userspec, hostname, port)
        super(LocalDriver, self).__init__()

    def exec_command(self, *args, **kwargs):
        return super(LocalDriver, self).exec_command(['ssh', '-t', self._target] + list(args)])


class SSHDriver(Driver):
    def __init__(self, hostname, username=None, port=22, use_paramiko=True):
        super(Driver, self).__init__()
        if use_paramiko:
            self._connection = ParamikoConnection(hostname, username=username, port=port)
        else:
            self._connection = SSHConnection(hostname, username=username, port=port)

    def exec_command(self, *args, **kwargs):
        return self._connection.exec_command(*args, **kwargs)
