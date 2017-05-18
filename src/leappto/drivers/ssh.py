import os
import shlex
import json
from paramiko import AutoAddPolicy, SSHClient, SSHConfig


class Driver(object):
    pass


class SSHDriver(Driver):
    def __init__(self, client=None):
        self._client = client

    def connect(self, hostname, **kwargs):
        self._client = SSHClient()
        print json.dumps([{'hostname': hostname}, kwargs])
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(AutoAddPolicy())
        self._client.connect(hostname, **kwargs)

    @property
    def transport(self):
        return self._client

    # FIXME: This is a short cut, eventually this should be abstracted away
    #        and not exposed
    def open_ftp(self):
        return self.transport.open_sftp()

    # FIXME: This is a short cut, eventually this should be abstracted away
    #        and not exposed
    def exec_command(self, command, *args, **kwargs):
        return self.transport.exec_command(command, *args, **kwargs)


class SSHVagrantDriver(SSHDriver):
    def __init__(self, domain_name):
        super(SSHVagrantDriver, self).__init__(None)
        print "SSHVagrantDriver with domain name:", domain_name
        self._domain_name = domain_name
        args = self._get_vagrant_ssh_args()
        if args:
            self.connect(args.pop('hostname'), **args)

    def _get_vagrant_data_path(self):
        index_path = os.path.join(os.environ['HOME'], '.vagrant.d/data/machine-index/index')
        index = json.load(open(index_path, 'r'))
        for ident, machine in index['machines'].iteritems():
            path_name = os.path.basename(machine['vagrantfile_path'])
            vagrant_name = machine.get('name', 'default')
            if self._domain_name == path_name + '_' + vagrant_name or self._domain_name == path_name:
                return machine['local_data_path']
        return None

    def _get_vagrant_ssh_args(self):
        path = self._get_vagrant_data_path()
        path = os.path.join(path, 'provisioners/ansible/inventory/vagrant_ansible_inventory')
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line[0] in (';', '#'):
                    continue
                return self._parse_ansible_inventory_data(line)
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
