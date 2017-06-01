"""LeApp CLI implementation"""

from argparse import ArgumentParser
from getpass import getpass
from grp import getgrnam, getgrgid
from json import dumps
from pwd import getpwuid
from subprocess import Popen, PIPE
from collections import OrderedDict
from leappto.providers.libvirt_provider import LibvirtMachineProvider, LibvirtMachine
from leappto.version import __version__
import os
import sys
import socket
import nmap
import shlex
import shutil

VERSION='leapp-tool {0}'.format(__version__)

# Python 2/3 compatibility
try:
    _set_inheritable = os.set_inheritable
except AttributeError:
    _set_inheritable = None

# Checking for required permissions
_REQUIRED_GROUPS = ["vagrant", "libvirt"]
def _user_has_required_permissions():
    """Check user has necessary permissions to reliably run leapp-tool"""
    uid = os.getuid()
    if uid == 0:
        # root has the necessary access regardless of group membership
        return True
    user_info = getpwuid(uid)
    user_name = user_info.pw_name
    user_group = getgrgid(user_info.pw_gid).gr_name
    for group in _REQUIRED_GROUPS:
        if group != user_group and user_name not in getgrnam(group).gr_mem:
            return False
    return True

# Parsing CLI arguments
def _add_identity_options(cli_cmd):
    cli_cmd.add_argument('--identity', default=None, help='Path to private SSH key')
    cli_cmd.add_argument('--ask-pass', '-k', action='store_true', help='Ask for SSH password')
    cli_cmd.add_argument('--user', '-u', default=None, help='Connect as this user')

def _make_argument_parser():
    ap = ArgumentParser()
    ap.add_argument('-v', '--version', action='version', version=VERSION, help='display version information')
    parser = ap.add_subparsers(help='sub-command', dest='action')

    list_cmd = parser.add_parser('list-machines', help='list running virtual machines and some information')
    migrate_cmd = parser.add_parser('migrate-machine', help='migrate source VM to a target container host')
    destroy_cmd = parser.add_parser('destroy-containers', help='destroy existing containers on virtual machine')
    scan_ports_cmd = parser.add_parser('port-inspect', help='scan ports on virtual machine')
    list_cmd.add_argument('--shallow', action='store_true', help='Skip detailed scans of VM contents')
    list_cmd.add_argument('pattern', nargs='*', default=['*'], help='list machines matching pattern')

    def _port_spec(arg):
        """Converts a port forwarding specifier to a (host_port, container_port) tuple

        Specifiers can be either a simple integer, where the host and container port are
        the same, or else a string in the form "host_port:container_port".
        """
        host_port, sep, container_port = arg.partition(":")
        host_port = int(host_port)
        if not sep:
            container_port = host_port
            host_port = None
        else:
            container_port = int(container_port)
        return host_port, container_port

    migrate_cmd.add_argument('machine', help='source machine to migrate')
    migrate_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    migrate_cmd.add_argument(
        '--tcp-port',
        default=None,
        dest="forwarded_ports",
        nargs='*',
        type=_port_spec,
        help='Target ports to forward to macrocontainer (temporary!)'
    )
    migrate_cmd.add_argument(
        '--use-rsync',
        action='store_true',
        help='use rsync as backend for filesystem migration, otherwise virt-tar-out'
    )
    _add_identity_options(migrate_cmd)

    destroy_cmd.add_argument('target', help='target VM name')
    _add_identity_options(destroy_cmd)

    scan_ports_cmd.add_argument('address', help='virtual machine address')
    scan_ports_cmd.add_argument(
        '--range',
        default=None,
        help='port range, example of proper form:"-100,200-1024,T:3000-4000,U:60000-"'
    )
    scan_ports_cmd.add_argument(
        '--shallow',
        action='store_true',
        help='Skip detailed informations about used ports, this is quick SYN scan'
    )
    return ap

# Run the CLI
def main():
    if not _user_has_required_permissions():
        msg = "Run leapp-tool as root, or as a member of all these groups: "
        print(msg + ",".join(_REQUIRED_GROUPS))
        exit(-1)

    ap = _make_argument_parser()

    def _find_machine(ms, name):
        for machine in ms:
            if machine.hostname == name:
                return machine
        return None

    def _set_ssh_config(username, identity, use_sshpass=False):
        settings = {
            'StrictHostKeyChecking': 'no',
        }
        if use_sshpass:
            settings['PasswordAuthentication'] = 'yes'
        else:
            settings['PasswordAuthentication'] = 'no'
        if username is not None:
            if not isinstance(username, str):
                raise TypeError("username should be str")
            settings['User'] = username
        if identity is not None:
            if not isinstance(identity, str):
                raise TypeError("identity should be str")
            settings['IdentityFile'] = identity

        ssh_options = ['-o {}={}'.format(k, v) for k, v in settings.items()]
        return use_sshpass, ssh_options

    class MigrationContext:

        _SSH_CTL_PATH = '{}/.ssh/ctl'.format(os.environ['HOME'])
        _SSH_CONTROL_PATH = '-o ControlPath="{}/%L-%r@%h:%p"'.format(_SSH_CTL_PATH)

        def __init__(self, source, target, ssh_settings, disk, forwarded_ports=None, rsync_cp_backend=False):
            self.source = source
            self.target = target
            self.use_sshpass, self.ssh_cfg = ssh_settings
            self._cached_ssh_password = None
            self.disk = disk
            self.rsync_cp_backend = rsync_cp_backend
            if forwarded_ports is None:
                forwarded_ports = [(80, 80)]  # Default to forwarding plain HTTP
            else:
                forwarded_ports = list(forwarded_ports)
            self.forwarded_ports = forwarded_ports

        def __get_machine_addr(self, machine):
            # We assume the source/target to be an IP or FQDN if not a machine name
            return machine.ip[0] if isinstance(machine, LibvirtMachine) else machine

        @property
        def target_addr(self):
            return self.__get_machine_addr(self.target)

        @property
        def source_addr(self):
            return self.__get_machine_addr(self.source)

        def _ssh_base(self, addr=None):
            if addr is None:
                addr = self.target_addr
            return ['ssh'] + self.ssh_cfg + ['-4', addr]

        def _ssh(self, cmd, reuse_ssh_conn=False, addr=None, **kwargs):
            ssh_cmd = self._ssh_base(addr)
            if reuse_ssh_conn:
                ssh_cmd += [self._SSH_CONTROL_PATH]
            ssh_cmd += [cmd]
            if self.use_sshpass:
                return self._sshpass(ssh_cmd, **kwargs)
            return Popen(ssh_cmd, **kwargs).wait()

        def _open_permanent_ssh_conn(self, addr):
            if not os.path.exists(self._SSH_CTL_PATH):
                try:
                    os.makedirs(self._SSH_CTL_PATH)
                except OSError as exc:
                    if exc.errno != 17:
                        raise

            cmd = 'ssh -nNf -o ControlMaster=yes {} {} -4 {}'.format(self._SSH_CONTROL_PATH, ' '.join(self.ssh_cfg), addr)
            return Popen(shlex.split(cmd)).wait()

        def _close_permanent_ssh_conn(self, addr):
            cmd = 'ssh {} {} -O exit {}'.format(self._SSH_CONTROL_PATH, ' '.join(self.ssh_cfg), addr)
            return Popen(shlex.split(cmd)).wait()

        def _sshpass(self, ssh_cmd, **kwargs):
            read_pwd, write_pwd = os.pipe()
            if _set_inheritable is not None:
                # To reduce risk of data leaks, Py3 FD inheritance is explicit
                _set_inheritable(read_pwd)
                kwargs = kwargs.copy()
                kwargs['pass_fds'] = (read_pwd,)
            sshpass_cmd = ['sshpass', '-d'+str(read_pwd)] + ssh_cmd
            child = Popen(sshpass_cmd, **kwargs)
            ssh_password = self._cached_ssh_password
            if ssh_password is None:
                ssh_password = self._cached_ssh_password = getpass("SSH password:").encode()
            os.write(write_pwd, ssh_password  + b'\n')
            return child.wait()

        def _ssh_sudo(self, cmd, **kwargs):
            return self._ssh("sudo bash -c '{}'".format(cmd), **kwargs)

        def copy(self):

            def _rsync():
                rsync_dir = '/opt/leapp-to/container'

                try:
                    os.makedirs(rsync_dir)
                except OSError as exc:
                    if exc.errno != 17:  # raise exception if it's different than FileExists
                        raise

                self._open_permanent_ssh_conn(self.source_addr)
                try:
                    self._ssh_sudo('sync && fsfreeze -f /', reuse_ssh_conn=True, addr=self.source_addr)

                    source_cmd = 'sudo rsync --rsync-path="sudo rsync" -aAX -r'
                    for exd in ['/dev/*', '/proc/*', '/sys/*', '/tmp/*', '/run/*', '/mnt/*', '/media/*', '/lost+found/*']:
                        source_cmd += ' --exclude=' + exd
                    source_cmd += ' -e "ssh {} {}" {}:/ {}'.format(
                        self._SSH_CONTROL_PATH, ' '.join(self.ssh_cfg), self.source_addr, rsync_dir
                    )

                    Popen(shlex.split(source_cmd)).wait()
                finally:
                    self._ssh_sudo('fsfreeze -u /', reuse_ssh_conn=True, addr=self.source_addr)
                    self._close_permanent_ssh_conn(self.source_addr)

                # if it's localhost this should not be executed
                # and it would be useful to check if source and target are in the same network
                # if yes then source -> rsync -> custom target
                if self.target_addr not in ['127.0.0.1', 'localhost']:
                    target_cmd = 'sudo rsync -aAX --rsync-path="sudo rsync" -r {0}/ -e "ssh {1}" {2}:{0}' \
                                 .format(rsync_dir, ' '.join(self.ssh_cfg), self.target_addr)
                    Popen(shlex.split(target_cmd)).wait()
                    shutil.rmtree(rsync_dir)

            def _virt_tar_out():
                try:
                    print('! ', self.source.suspend())
                    # Vagrant always uses qemu:///system, so for now, we always run
                    # virt-tar-out as root, rather than as the current user
                    proc = Popen(['sudo', 'bash', '-c', 'LIBGUESTFS_BACKEND=direct virt-tar-out -a {} / -' \
                                .format(self.disk)], stdout=PIPE)
                    return self._ssh_sudo(
                        'cat > /opt/leapp-to/container.tar.gz && tar xf /opt/leapp-to/container.tar.gz -C ' + \
                        '/opt/leapp-to/container', stdin=proc.stdout
                    )
                finally:
                    print('! ', self.source.resume())

            self._ssh_sudo('docker rm -f container 2>/dev/null 1>/dev/null ; rm -rf /opt/leapp-to/container; ' + \
                           'mkdir -p /opt/leapp-to/container')
            if self.rsync_cp_backend:
                return _rsync()
            return _virt_tar_out()

        def destroy_containers(self):
            command = 'docker rm -f $(docker ps -q) 2>/dev/null 1>/dev/null; rm -rf /opt/leapp-to/container'
            return self._ssh_sudo(command)

        def start_container(self, img, init):
            # remove unpacking and removing container dir to copy function
            command = 'docker run -tid' + \
                    ' -v /sys/fs/cgroup:/sys/fs/cgroup:ro'
            good_mounts = ['bin', 'etc', 'home', 'lib', 'lib64', 'media', 'opt', 'root', 'sbin', 'srv', 'usr', 'var']
            for mount in good_mounts:
                command += ' -v /opt/leapp-to/container/{m}:/{m}:Z'.format(m=mount)
            for host_port, container_port in self.forwarded_ports:
                if host_port is None:
                    command += ' -p {:d}'.format(container_port)  # docker will select random port for host
                else:
                    command += ' -p {:d}:{:d}'.format(host_port, container_port)
            command += ' --name container ' + img + ' ' + init
            return self._ssh_sudo(command)

        def _fix_container(self, fix_str):
            return self._ssh_sudo('docker exec -t container {}'.format(fix_str))

        def fix_upstart(self):
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/httpd && ' + \
                    '(service mysqld start && ' + \
                    'service httpd start) 2>/dev/null ;' + \
                    '(service drools stop ; service drools start) 2>/dev/null 1>&2"'
            return self._fix_container(fixer)

        def fix_systemd(self):
            # systemd cleans /var/log/ and mariadb & httpd can't handle that, might be a systemd bug
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/{httpd,mariadb} && ' + \
                    'chown mysql:mysql /var/log/mariadb && ' + \
                    'systemctl enable httpd mariadb ; ' + \
                    'systemctl start httpd mariadb"'
            return self._fix_container(fixer)


    parsed = ap.parse_args()
    if parsed.action == 'list-machines':
        lmp = LibvirtMachineProvider(parsed.shallow)
        print(dumps({'machines': [m._to_dict() for m in lmp.get_machines()]}, indent=3))

    elif parsed.action == 'migrate-machine':
        if not parsed.target:
            print('! no target specified, creating leappto container package in current directory')
            # TODO: not really for now
            raise NotImplementedError
        else:
            source = parsed.machine
            target = parsed.target
            forwarded_ports = parsed.forwarded_ports

            print('! looking up "{}" as source and "{}" as target'.format(source, target))

            lmp = LibvirtMachineProvider()
            machines = lmp.get_machines()

            machine_src = _find_machine(machines, source)
            machine_dst = _find_machine(machines, target)

            ip = machine_dst.ip[0] if machine_dst else target

            if not machine_src:
                print("Machine is not ready:")
                print("Source: " + repr(machine_src))
                exit(-1)

            print('! configuring SSH keys')
            # pass source machine ip
            mc = MigrationContext(
                machine_src,
                machine_dst,
                _set_ssh_config(parsed.user, parsed.identity, parsed.ask_pass),
                machine_src.disks[0].host_path,
                forwarded_ports,
                parsed.use_rsync
            )
            print('! copying over')
            mc.copy()
            print('! provisioning ...')
            # if el7 then use systemd
            if machine_src.installation.os.version.startswith('7'):
                result = mc.start_container('centos:7', '/usr/lib/systemd/systemd --system')
                print('! starting services')
                mc.fix_systemd()
            else:
                result = mc.start_container('centos:6', '/sbin/init')
                print('! starting services')
                mc.fix_upstart()
            print('! done')
            sys.exit(result)

    elif parsed.action == 'destroy-containers':
        target = parsed.target

        lmp = LibvirtMachineProvider()
        machines = lmp.get_machines()

        machine_dst = _find_machine(machines, target)

        print('! looking up "{}" as target'.format(target))
        print('! configuring SSH keys')
        mc = MigrationContext(
            None,
            machine_dst,
            _set_ssh_config(parsed.user, parsed.identity, parsed.ask_pass),
            None
        )

        print('! destroying containers on "{}" VM'.format(target))
        result = mc.destroy_containers()
        print('! done')
        sys.exit(result)

    elif parsed.action == 'port-inspect':
        _ERR_STATE = "error"
        _SUCCESS_STATE = "success"

        scan_args = '-sS' if parsed.shallow else '-sV'

        port_range = parsed.range
        ip = socket.gethostbyname(parsed.address)
        port_scanner = nmap.PortScanner()
        port_scanner.scan(ip, port_range, arguments=scan_args)

        result = {
            "status": _SUCCESS_STATE,
            "err_msg": "",
            "ports": OrderedDict()
        }

        scan_info = port_scanner.scaninfo()
        if scan_info.get('error', False):
            result["status"] = _ERR_STATE
            result["err_msg"] = scan_info['error'][0] if isinstance(scan_info['error'], list) else scan_info['error']
            print(dumps(result, indent=3))
            exit(-1)

        if ip not in port_scanner.all_hosts():
            result["status"] = _ERR_STATE
            result["err_msg"] = "Machine {} not found".format(ip)
            print(dumps(result, indent=3))
            exit(-1)

        for proto in port_scanner[ip].all_protocols():
            result['ports'][proto] = OrderedDict()
            for port in sorted(port_scanner[ip][proto]):
                if port_scanner[ip][proto][port]['state'] != 'open':
                    continue
                result['ports'][proto][port] = port_scanner[ip][proto][port]

        print(dumps(result, indent=3))
