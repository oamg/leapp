"""LeApp CLI implementation"""

from argparse import ArgumentParser
from grp import getgrnam, getgrgid
from json import dumps, loads
from os import getuid, pipe, read, path
from tempfile import NamedTemporaryFile, mkdtemp
from pwd import getpwuid
from subprocess import Popen, PIPE, check_output
from collections import OrderedDict, namedtuple
from leappto.providers.libvirt_provider import LibvirtMachineProvider
from leappto.version import __version__
import sys
import nmap
import time


# ssh -o IdentityFile=/home/podvody/Repos/leapp-proto/demo/vmdefs/centos7-mezzanine/.vagrant/machines/default/libvirt/private_key -o PasswordAuthentication=no -o StrictHostKeyChecking=no -o User=vagrant -4 192.168.121.251 sudo -u postgres PGPASSWORD=meza007 pg_dump -F t -U meza db | oc exec -i postgresql-1-qm3mx -- bash -c 'pg_restore -C -d postgres -F t'

DatabaseInfo = namedtuple('DatabaseInfo', ['name', 'username', 'password'])


def _ssh_config(username, identity):
    assert username is not None and isinstance(username, str), "username should be str or None"
    assert isinstance(identity, str), "identity should be str"

    settings = {
        'StrictHostKeyChecking': 'no',
        'PasswordAuthentication': 'no',
        'IdentityFile': identity,
    }
    if username is not None:
        settings['User'] = username

    return ['-o {}={}'.format(k, v) for k, v in settings.items()]


def _ssh_base(cfg, tgt):
    return ['ssh'] + cfg + ['-4', tgt]


def _ssh(cfg, tgt, cmd, **kwargs):
    arg = _ssh_base(cfg, tgt) + cmd
    print(" ".join(arg))
    return Popen(arg, **kwargs).wait()

def _ssh_output(cfg, tgt, cmd):
    arg = _ssh_base(cfg, tgt) + cmd
    return check_output(arg)


def get_value(obj, pathspec, default=None, strict=False):
    if '.' not in pathspec and pathspec not in obj:
        if strict:
            raise ValueError('pathspec: "{}" is invalid'.format(pathspec))
        return default
    bound = obj
    for item in pathspec.split('.'):
        if item in bound:
            bound = bound[item]
        else:
            if strict:
                raise ValueError('pathspec: "{}" is invalid'.format(pathspec))
            return default
    return bound


def get_items(obj, *items):
    i = []
    for item in items:
        i.append(obj[item])
    return i


def get_db_connection(db_info):
    return DatabaseInfo(*get_items(db_info, 'NAME', 'USER', 'PASSWORD'))


def get_data_from_metadata(metadata):
    # handle only the first django element
    db_dict = get_value(metadata['django'][0], 'data.db.default')
    return get_db_connection(db_dict)


def migrate_microservices(source_ip, target_ip, openshift, identity, user):
    ANALYZER_PATH = '/opt/leapp-to/analyzers/django'

    os_user, os_pw = openshift.split(':')

    ssh_config = _ssh_config(user, identity)

    def scp(src, dst, **kwargs):
        return Popen(['scp', '-r'] + ssh_config + [src, dst], **kwargs).wait()

    def ssh(cmd, **kwargs):
        return _ssh(ssh_config, source_ip, cmd, **kwargs)

    def ssh_output(cmd):
        return _ssh_output(ssh_config, source_ip, cmd)

    def oc(cmd, **kwargs):
        print('oc ' + ' '.join(cmd))
        return Popen(['oc'] + cmd, **kwargs).wait()

    def oc_process_apply(variables, file):
        proc = ['oc', 'process', '-f', file]
        for var in variables:
            proc += ['-v', var]
        p = Popen(proc, stdout=PIPE)
        apply = ['oc', 'apply', '-f', '-']
        a = Popen(apply, stdin=p.stdout).wait()
        p.wait()

    def oc_get_pod_name(selector):
        sel = ["oc", "get", "-o", "jsonpath", "pod",
               "--selector=name={}".format(selector),
               "--template={.items[*].metadata.name}"]
        return check_output(sel)


    print('! Creating remote tmp dir')
    ## = COPY IN THE DATA ====================================================
    tmp_dir = ssh_output(['mktemp', '-d']).strip()
    print('! Copying analyzer into remote tmp dir: {}'.format(tmp_dir))
    scp(ANALYZER_PATH, source_ip+':'+tmp_dir)

    ## = EXECUTE ANALYZER ====================================================
    print('! Executing analuzer remotely')
    metadata = loads(ssh_output(['python ' + path.join(tmp_dir, 'django/django_analyzer_impl.py')]))
    import pprint
    print('! Analyzer data:')
    pprint.pprint(metadata)

    print('! Connecting to OpenShift: {}@{}'.format(os_user, target_ip))
    oc(['login', '-u', os_user, '-p', os_pw, 'https://{}:8443/'.format(target_ip)])


    ## = USE DATA ============================================================
    db_conn = get_data_from_metadata(metadata)

    print('! Starting PostgreSQL Pod & Services')
    oc_process_apply([], '/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-memcached.yaml')
    oc_process_apply(['POSTGRESQL_VERSION=9.2'], '/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-postgresql.yaml')
    
    pgsql_pod = None
    deadline = time.time() + 120
    next_message = time.time() + 2
    print('! Waiting for PostgreSQL pod to become active ...')
    while True:
        if time.time() >= deadline:
            break
        if time.time() >= next_message:
            print(' > still waiting')
            next_message = time.time() + 2
        pgsql_pod = oc_get_pod_name('postgresql')
        time.sleep(1)
        if pgsql_pod:
            break

    print('! Waiting for the pod to become ready ...')
    time.sleep(30)
    print('! Running PostgreSQL pod: ' + pgsql_pod)
    create_user = 'PGPASSWORD={pw} createuser {un}'.format(pw=db_conn.password, un=db_conn.username)
    oc(['exec', pgsql_pod, '--', 'bash', '-c', create_user])

    with NamedTemporaryFile() as tmp:
        cmd = 'sudo -u {s_user} PGPASSWORD={d_password} pg_dump -F t -U {d_user} {d_name}'
        fmt = {
            's_user': 'postgres',
            'd_user': db_conn.username,
            'd_name': db_conn.name,
            'd_password': db_conn.password
        }
        ssh([cmd.format(**fmt)], stdout=tmp)
        print('! Database backup snapshotted in: {} ({} bytes) '.format(tmp.name, path.getsize(tmp.name)))

        tmp.seek(0)
        cmd = '/opt/rh/postgresql92/root/usr/bin/pg_restore -C -d postgres'
        oc(['exec', '-i', pgsql_pod, '--', 'bash', '-c', "pg_restore -C -d postgres -F t"], stdin=tmp)
        print('! Setting password for user: meza')
        oc(['exec', '-i', pgsql_pod, '--', 'bash', '-c', 'psql -c "ALTER USER meza PASSWORD \'meza007\';"'], stdin=tmp)

    ## =======================================================================
    print('! Copying application source to artifacts')
    src_path = metadata['django'][0]['path']
    app_source_dir = mkdtemp()
    scp(source_ip+':'+src_path, app_source_dir)

    arr = ['sed', '-i', 's/MIDDLEWARE_CLASSES/MIDDLEWARE/g', path.join(app_source_dir, 'blog/blog', 'settings.py')]
    print(arr)
    check_output(arr)
    print('! Updating configuration before deployment')
    mocked_settings_py = path.relpath(metadata['django'][0]['settings'][0], src_path)
    with open(path.join(app_source_dir, 'blog', mocked_settings_py), 'w+') as spy:
        print('! Updated file: \n' + pprint.pformat(metadata['django'][0]['deploy_settings']))
        spy.write(metadata['django'][0]['deploy_settings'][0]['detail'])
    ## =======================================================================

    print('! Compressing sources\n' + check_output(['tar', '--format=gnu', '-cvf', '/tmp/deploy.tar', '-C', app_source_dir+'/'+'blog/', '.']))

    print('! Executing S2I Build')
    oc(['new-build', '--strategy=source', '--docker-image=centos/python-27-centos7', '--to=django-mezza', app_source_dir+'/'+'blog/'])
    time.sleep(2)
    oc(['start-build', '--from-dir=/tmp/deploy.tar', 'django-mezza'])
    print('! Listening to build events ...')
    oc(['logs', '-f', 'django-mezza-1-build'])
    oc(['new-app', 'django-mezza'])
    oc(['expose', 'service', '--port', '80', '--path', '/', 'django-mezza'])
    oc(['get', 'route'])
    ## =======================================================================


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
    microservices_cmd = parser.add_parser('microservices', help='migrate source VM to a target OpenShift cluster')

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

    microservices_cmd.add_argument('source', help='source machine to migrate')
    microservices_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    microservices_cmd.add_argument('-o', '--openshift-credentials', default='developer:developer', help='credentials to use to access target OpenShift cluster in the username:password format')
    _add_identity_options(microservices_cmd)

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
        if not isinstance(identity, str):
            raise TypeError("identity should be str")
        settings = {
            'StrictHostKeyChecking': 'no',
            'PasswordAuthentication': 'no',
            'IdentityFile': identity,
        }
        if username is not None:
            if not isinstance(username, str):
                raise TypeError("username should be str")
            settings['User'] = username

        return ['-o {}={}'.format(k, v) for k, v in settings.items()]

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
            # Vagrant always uses qemu:///system, so for now, we always run
            # virt-tar-out as root, rather than as the current user
            proc = Popen(['sudo', 'virt-tar-out', '-a', self.disk, '/', '-'], stdout=PIPE)
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

            mc = MigrationContext(
                ip,
                _set_ssh_config(parsed.user, parsed.identity),
                machine_src.disks[0].host_path,
                forwarded_ports
            )
            print('! copying over')
            print('! ' + machine_src.suspend())
            mc.copy()
            print('! ' + machine_src.resume())
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

        mc = MigrationContext(
            ip,
            _set_ssh_config(parsed.user, parsed.identity),
            machine_dst.disks[0].host_path
        )

        print('! destroying containers on "{}" VM'.format(target))
        mc.destroy_containers()
        print('! done')

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

    elif parsed.action == 'microservices':
        source = parsed.source
        target = parsed.target
        openshift = parsed.openshift_credentials

        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")

        print('! looking up "{}" as source and "{}" as target'.format(source, target))

        lmp = LibvirtMachineProvider()
        machines = lmp.get_machines()

        machine_dst = _find_machine(machines, target)
        machine_src = _find_machine(machines, source)

        src_ip, dst_ip = machine_src.ip[0], machine_dst.ip[0]

        print(' > breaking up monolith at {} into microservices in {}'.format(src_ip, dst_ip))

        migrate_microservices(src_ip, dst_ip, openshift, parsed.identity, parsed.user)
