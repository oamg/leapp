"""LeApp CLI implementation"""

from argparse import ArgumentParser
from grp import getgrnam, getgrgid
from json import dumps
from os import getuid
from pwd import getpwuid
from subprocess import Popen, PIPE
from collections import OrderedDict
from leappto.providers.libvirt_provider import LibvirtMachineProvider
from leappto.version import __version__
import leappto.actors.load
from leappto.actors.meta import registry
from leappto.actors.meta import registry
from leappto.actors.meta.resolver import resolve as meta_resolve
from leappto.actors.meta.resolver import dependency_ordered as meta_dependency_ordered
from leappto.drivers.ssh import SSHDriver, SSHVagrantDriver
import sys
import nmap


VERSION='leapp-tool {0}'.format(__version__)

# Checking for required permissions
_REQUIRED_GROUPS = ["vagrant", "libvirt"]
def _user_has_required_permissions():
    """Check user has necessary permissions to reliably run leapp-tool"""
    uid = getuid()
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
    migrate_cmd.add_argument('-o', '--ovirt', default=False, help='Use ovirt spike mechanism')
    migrate_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    migrate_cmd.add_argument(
        '--tcp-port',
        default=None,
        dest="forwarded_ports",
        nargs='*',
        type=_port_spec,
        help='Target ports to forward to macrocontainer (temporary!)'
    )
    _add_identity_options(migrate_cmd)

    destroy_cmd.add_argument('target', help='target VM name')
    _add_identity_options(destroy_cmd)

    scan_ports_cmd.add_argument('range', help='port range, example of proper form:"-100,200-1024,T:3000-4000,U:60000-"')
    scan_ports_cmd.add_argument('ip', help='virtual machine ip address')
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

    def _set_ssh_config(username, identity):
        settings = {
            'StrictHostKeyChecking': 'no',
            'PasswordAuthentication': 'no',
        }
        if username is not None:
            if not isinstance(username, str):
                raise TypeError("username should be str")
            settings['User'] = username
        if identity is not None:
            if not isinstance(identity, str):
                raise TypeError("identity should be str")
            settings['IdentityFile'] = identity

        return ['-o {}={}'.format(k, v) for k, v in settings.items()]

    class MigrationContext:
        def __init__(self, target, user, identity_file, disk, forwarded_ports=None, machine_src=None):
            self.target = target
            self.target_cfg = _set_ssh_config(user, identity_file)
            self.disk = disk
            if forwarded_ports is None:
                forwarded_ports = [(80, 80)]  # Default to forwarding plain HTTP
            else:
                forwarded_ports = list(forwarded_ports)
            self.forwarded_ports = forwarded_ports
            self._src_drv = SSHVagrantDriver(machine_src.hostname)
            self._dst_drv = SSHDriver(None)
            self._dst_drv.connect(self.target, key_filename=identity_file, username=user or 'vagrant')

        @property
        def _ssh_base(self):
            return ['ssh'] + self.target_cfg + ['-4', self.target]

        def _ssh(self, cmd, **kwargs):
            arg = self._ssh_base + [cmd]
            return Popen(arg, **kwargs).wait()

        def _ssh_sudo(self, cmd, **kwargs):
            return self._ssh("sudo bash -c '{}'".format(cmd), **kwargs)

        def copy(self):
            # Vagrant always uses qemu:///system, so for now, we always run
            # virt-tar-out as root, rather than as the current user
            proc = Popen(['sudo', 'virt-tar-out', '-a', self.disk, '/', '-'], stdout=PIPE)
            return self._ssh('cat > /opt/leapp-to/container.tar.gz', stdin=proc.stdout)

        def destroy_containers(self):
            command = 'docker rm -f $(docker ps -q) 2>/dev/null 1>/dev/null; rm -rf /opt/leapp-to/container'
            return self._ssh_sudo(command)

        def analyze_services(self):
            print '! analyzing services'
            _, out, _ = self._src_drv.exec_command("systemctl list-unit-files | grep enabled | grep \\.service | cut -f1 -d\\ ")
            enabled = []
            service_mapping = {'{}.service'.format(service): cls for cls in registry() for service in cls.leapp_meta().get('services', [])}
            from pprint import pprint
            pprint(service_mapping)
            for service in out.read().split():
                print '! processing service name:', service
                cls = service_mapping.get(service)
                if cls:
                    print '!', service, 'handled by', cls.__name__
                    enabled.append(cls)
            pprint(enabled)
            print '! services analyzed'
            return enabled

        @staticmethod
        def _get_run_systemd_service_cmd(service):
            return "/bin/bash /sbin/leapp-init " + service

        def create_systemd_containers(self, services):
            # self._ssh_sudo(self._prep_container_command())
            ftp = self._dst_drv.open_ftp()
            with ftp.file('/opt/leapp-to/leapp-init', 'w') as f:
                f.write('''#!/bin/bash

[[ -f /sbin/leapp-init-prepare ]] && /bin/bash /sbin/leapp-init-prepare

SERVICE_NAME=$1.service
SVCTYPE=$(grep ^Type= `find /etc/systemd/system -name $SERVICE_NAME` | cut -d= -f2-)
SERVICE_USER=$(grep ^User= `find /etc/systemd/system -name $SERVICE_NAME` | cut -d= -f2-)
if [[ ! -z "$SERVICE_USER" ]] && [[ "$SERVICE_USER" != "$USER" ]]; then
        echo $SERVICE_USER;
        sudo -u $SERVICE_USER /sbin/leapp-init $1;
        exit $?;
fi
eval $(grep ^Environment= `find /etc/systemd/system -name $SERVICE_NAME` | cut -d= -f2-)
for EFILE in $(grep ^EnvironmentFile= `find /etc/systemd/system -name $SERVICE_NAME` | cut -d= -f2-); do
        EFILE=$(echo $EFILE | sed "s/^-//");
        if [ -f $EFILE ]; then
                source $EFILE;
        fi
done;

rm -f /tmp/leappd-init.notify;
python -c "import os, socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); s.bind('/tmp/leappd-init.notify'); os.chmod('/tmp/leappd-init.notify', 0777); s.recv(1024)" &

export NOTIFY_SOCKET=/tmp/leappd-init.notify;

eval $(grep ^ExecStartPre= `find /etc/systemd/system -name $SERVICE_NAME` | cut -d= -f2-);
eval $(grep ^ExecStart= `find /etc/systemd/system -name $SERVICE_NAME` | cut -d= -f2-);

[[ "$SVCTYPE" == "forking" ]] && /usr/bin/sleep infinity;

''')
            meta_resolve(services)
            mapped = registry(mapped=True)
            services = meta_dependency_ordered(services)
            from pprint import pprint
            print "! Resolved service dependencies"
            pprint(services)
            for svc in services:
                smeta = svc.leapp_meta()
                sname = smeta['services'][0]
                svc(driver=self._dst_drv).fixup()
                opts = [' -v /opt/leapp-to/leapp-init:/sbin/leapp-init']
                if 'directories' in smeta or 'users' in smeta:
                    opts.append(' -v /opt/leapp-to/' + sname + '.prepare:/sbin/leapp-init-prepare')
                    with ftp.file('/opt/leapp-to/' + sname + '.prepare', 'w') as f:
                        for u in smeta.get('users', ()):
                            f.write('\ngetent passwd {user} > /dev/null || useradd -o -r {user} -s /sbin/nologin;\n'.format(user=u))
                        for d in smeta.get('directories', ()):
                            f.write('\nmkdir -p {path}; chown {user}:{group} {path}; chmod {mode} {path}\n'.format(**d))
                for link in smeta.get('require_links', ()):
                    print "opts for link", link
                    opts.append(' --link container-' + mapped[link['target']].leapp_meta()['services'][0])
                self.start_container(
                        'centos:7', self._get_run_systemd_service_cmd(sname),
                        forwarded_ports=[(port, port) for port in smeta.get('ports', ())],
                        name='container-' + sname, exec_prep=False, opts=opts)
            ftp.close()

        def _prep_container_command(self):
            command = 'rm -rf /opt/leapp-to/container ;' + \
                    'mkdir -p /opt/leapp-to/container && ' + \
                    'tar xf /opt/leapp-to/container.tar.gz -C /opt/leapp-to/container'
            return command

        def start_container(self, img, init, forwarded_ports=None, name='container', opts='', exec_prep=True):
            command = 'docker rm -f ' + name + ' 2>/dev/null 1>/dev/null ; '
            if exec_prep:
                command += self._prep_container_command() + '; '
            command += 'docker run -tid' + \
                    ' -v /sys/fs/cgroup:/sys/fs/cgroup:ro'
            good_mounts = ['bin', 'etc', 'home', 'lib', 'lib64', 'media', 'opt', 'root', 'sbin', 'srv', 'usr', 'var']
            for mount in good_mounts:
                command += ' -v /opt/leapp-to/container/{m}:/{m}:Z'.format(m=mount)
            for host_port, container_port in forwarded_ports:
                if host_port is None:
                    command += ' -p {:d}'.format(container_port)  # docker will select random port for host
                else:
                    command += ' -p {:d}:{:d}'.format(host_port, container_port)
            if opts:
                command += ' ' + ' '.join(opts)
            command += ' --name ' + name + ' ' + img + ' ' + init

            print "Starting container\n----------------------------------\n",command,"\n------------------------------------------------"
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
            ovirt = parsed.ovirt
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

            mc = MigrationContext(
                ip,
                parsed.user,
                parsed.identity,
                machine_src.disks[0].host_path,
                forwarded_ports=forwarded_ports,
                machine_src=machine_src
            )
            print('! copying over')
            if not ovirt:
                print('! ' + machine_src.suspend())
                mc.copy()
                print('! ' + machine_src.resume())
            print('! provisioning ...')
            # if ovirt use detection mechanism
            if ovirt:
                services = mc.analyze_services()
                print('! starting services')
                mc.create_systemd_containers(services)
                result = 0
            # if el7 then use systemd
            elif machine_src.installation.os.version.startswith('7'):
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
        if not machine_dst:
            print("Machine is not ready:")
            print("Target: " + repr(machine_dst))
            exit(-1)

        print('! configuring SSH keys')
        ip = machine_dst.ip[0]

        mc = MigrationContext(
            ip,
            _set_ssh_config(parsed.user, parsed.identity),
            machine_dst.disks[0].host_path
        )

        print('! destroying containers on "{}" VM'.format(target))
        result = mc.destroy_containers()
        print('! done')
        sys.exit(result)

    elif parsed.action == 'port-inspect':
        _ERR_STATE = "error"
        _SUCCESS_STATE = "success"

        port_range = parsed.range
        ip = parsed.ip
        port_scanner = nmap.PortScanner()
        port_scanner.scan(ip, port_range)

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
