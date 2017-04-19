"""LeApp CLI implementation"""

from argparse import ArgumentParser
from leappto.providers.libvirt_provider import LibvirtMachineProvider
from json import dumps
from os import getuid
from subprocess import Popen, PIPE
import sys


def main():
    if getuid() != 0:
        print("Please run me as root")
        exit(-1)

    ap = ArgumentParser()
    ap.add_argument('-v', '--version', action='store_true', help='display version information')
    parser = ap.add_subparsers(help='sub-command', dest='action')

    list_cmd = parser.add_parser('list-machines', help='list running virtual machines and some information')
    migrate_cmd = parser.add_parser('migrate-machine', help='migrate source VM to a target container host')
    destroy_cmd = parser.add_parser('destroy-containers', help='destroy existing containers on virtual machine')

    list_cmd.add_argument('--shallow', action='store_true', help='Skip detailed scans of VM contents')
    list_cmd.add_argument('pattern', nargs='*', default=['*'], help='list machines matching pattern')

    def _port_spec(arg):
        """Converts a port forwarding specifier to a (host_port, container_port) tuple

        Specifiers can be either a simple integer, where the host and container port are
        the same, or else a string in the form "host_port:container_port".
        """
        host_port, sep, container_port = arg.partition(":")
        host_port = int(host_port)
        if sep is None:
            container_port = host_port
        else:
            container_port = int(container_port)
        return host_port, container_port

    migrate_cmd.add_argument('machine', help='source machine to migrate')
    migrate_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    migrate_cmd.add_argument('--identity', default=None, help='Path to private SSH key')
    migrate_cmd.add_argument(
        '--tcp-port',
        default=None,
        dest="forwarded_ports",
        nargs='*',
        type=_port_spec,
        help='Target ports to forward to macrocontainer (temporary!)'
    )

    destroy_cmd.add_argument('target', help='target VM name')
    destroy_cmd.add_argument('--identity', default=None, help='Path to private SSH key')

    def _find_machine(ms, name):
        for machine in ms:
            if machine.hostname == name:
                return machine
        return None


    class MigrationContext:
        def __init__(self, target, target_cfg, disk, forwarded_ports=None):
            self.target = target
            self.target_cfg = target_cfg
            self.disk = disk
            if forwarded_ports is None:
                forwarded_ports = [(80, 80)]  # Default to forwarding plain HTTP
            else:
                forwarded_ports = list(forwarded_ports)
            forwarded_ports.append((9022, 22))  # Always forward SSH
            self.forwarded_ports = forwarded_ports

        @property
        def _ssh_base(self):
            return ['ssh'] + self.target_cfg + ['-4', self.target]

        def _ssh(self, cmd, **kwargs):
            arg = self._ssh_base + [cmd]
            return Popen(arg, **kwargs).wait()

        def _ssh_sudo(self, cmd, **kwargs):
            return self._ssh("sudo bash -c '{}'".format(cmd), **kwargs)

        def copy(self):
            proc = Popen(['virt-tar-out', '-a', self.disk, '/', '-'], stdout=PIPE)
            return self._ssh('cat > /opt/leapp-to/container.tar.gz', stdin=proc.stdout)

        def destroy_containers(self):
            command = 'docker rm -f $(docker ps -q) 2>/dev/null 1>/dev/null; rm -rf /opt/leapp-to/container'
            return self._ssh_sudo(command)

        def start_container(self, img, init):
            command = 'docker rm -f container 2>/dev/null 1>/dev/null ; rm -rf /opt/leapp-to/container ;' + \
                    'mkdir -p /opt/leapp-to/container && ' + \
                    'tar xf /opt/leapp-to/container.tar.gz -C /opt/leapp-to/container && ' + \
                    'docker run -tid' + \
                    ' -v /sys/fs/cgroup:/sys/fs/cgroup:ro'
            good_mounts = ['bin', 'etc', 'home', 'lib', 'lib64', 'media', 'opt', 'root', 'sbin', 'srv', 'usr', 'var']
            for mount in good_mounts:
                command += ' -v /opt/leapp-to/container/{m}:/{m}:Z'.format(m=mount)
            for host_port, container_port in self.forwarded_ports:
                command += ' -p {:d}:{:d}'.format(host_port, container_port)
            command += ' --name container ' + img + ' ' + init
            return self._ssh_sudo(command)

        def _fix_container(self, fix_str):
            return self._ssh_sudo('docker exec -t container {}'.format(fix_str))

        def fix_upstart(self):
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/httpd && ' + \
                    'service mysqld start && ' + \
                    'service httpd start"'
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
        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")

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

            if not machine_dst or not machine_src:
                print("Machines are not ready:")
                print("Source: " + repr(machine_src))
                print("Target: " + repr(machine_dst))
                exit(-1)

            print('! configuring SSH keys')
            ip = machine_dst.ip[0]
            target_ssh_config = [
                '-o User=vagrant',
                '-o StrictHostKeyChecking=no',
                '-o PasswordAuthentication=no',
                '-o IdentityFile=' + parsed.identity,
            ]

            mc = MigrationContext(
                ip,
                target_ssh_config,
                machine_src.disks[0].host_path,
                forwarded_ports
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
        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")
        target = parsed.target

        lmp = LibvirtMachineProvider()
        machines = lmp.get_machines()
        machine_dst = _find_machine(machines, target)

        print('! looking up "{}" as target'.format(target))
        if not machine_dst:
            print("Machine is not ready:")
            print("Target: " + repr(machine_dst))
            exit(-1)

        print('! configuring SSH keys')
        ip = machine_dst.ip[0]
        target_ssh_config = [
            '-o User=vagrant',
            '-o StrictHostKeyChecking=no',
            '-o PasswordAuthentication=no',
            '-o IdentityFile=' + parsed.identity,
        ]

        mc = MigrationContext(
            ip,
            target_ssh_config,
            machine_dst.disks[0].host_path
        )

        print('! destroying containers on "{}" VM'.format(target))
        mc.destroy_containers()
        print('! done')
