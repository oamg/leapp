from argparse import ArgumentParser
from leappto.providers.libvirt_provider import LibvirtMachineProvider
from json import dumps
from os import getuid
from subprocess import Popen, PIPE, check_output, CalledProcessError


def _get_ssh_config():
    ssh_kludge = {'target': '/root/leapp-to/rhel7-target', 'source': '/root/leapp-to/rhel6-guest-lamp'}
    out = {}
    for typ, path in ssh_kludge.iteritems():
        try:
            # bleak ugly code to convert SSH configuration file into bunch of `-o` flags for ssh
            out[typ] = ['-o {}={}'.format(*x.strip().split(' ')) for x in check_output(['vagrant', 'ssh-config'], cwd=path).decode('utf-8').splitlines()[1:-1]]
        except CalledProcessError:
            # domain probably not running
            pass
    return out



if getuid() != 0:
    print("Please run me as root")
    exit(-1)


ap = ArgumentParser()
ap.add_argument('-v', '--version', action='store_true', help='display version information')
parser = ap.add_subparsers(help='sub-command', dest='action')

list_cmd = parser.add_parser('list-machines', help='list running virtual machines and some information')
migrate_cmd = parser.add_parser('migrate-machine', help='migrate source VM to a target container host')

list_cmd.add_argument('pattern', nargs='*', default=['*'], help='list machines matching pattern')

migrate_cmd.add_argument('machine', help='source machine to migrate')
migrate_cmd.add_argument('-t', '--target', default=None, help='target VM name ')

def _find_machine(ms, name):
    for machine in ms:
        if machine.hostname == name:
            return machine
    return None

def _get_tar_stream(disk):
    return Popen(['virt-tar-out', '-a', disk, '/', '-'], stdout=PIPE)

def _copy_over(proc, target, target_cfg):
    return Popen(['ssh'] + target_cfg + ['-4', target, 'cat > /opt/leapp-to/container.tar.gz'], stdin=proc.stdout)

def _process_in_target(target, target_cfg):
    # I'm so sorry
    _systemd_cleanup = '(cd $PREFIX/lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done);(rm -f $PREFIX/lib/systemd/system/multi-user.target.wants/*;rm -f $PREFIX/etc/systemd/system/*.wants/*;rm -f $PREFIX/lib/systemd/system/local-fs.target.wants/*;rm -f $PREFIX/lib/systemd/system/sockets.target.wants/*udev*;rm -f $PREFIX/lib/systemd/system/sockets.target.wants/*initctl*;rm -f $PREFIX/lib/systemd/system/basic.target.wants/*;rm -f $PREFIX/lib/systemd/system/anaconda.target.wants/*)'
    extract = 'mkdir -p /opt/leapp-to/container && tar xf /opt/leapp-to/container.tar.gz -C /opt/leapp-to/container && '
    cleanup = 'export PREFIX=/opt/leapp-to/container && ' + _systemd_cleanup + ' && '
    docker_run = 'docker run -d'
    docker_run += ' -v /sys/fs/cgroup:/sys/fs/cgroup:ro' # CGroups
    good_mounts = ['bin', 'etc', 'home', 'lib', 'lib64', 'media', 'opt', 'root', 'sbin', 'srv', 'usr', 'var']
    #bad_mounts = ['boot', 'dev', 'proc', 'sys'] # pseudo file systems
    for mount in good_mounts:
        docker_run += ' -v /opt/leapp-to/container/{m}:/{m}:Z'.format(m=mount)
    docker_run += ' -p 9000:9000 centos:7 /usr/lib/systemd/systemd --system'
    return Popen(['ssh'] + target_cfg + ['-4', target, '"sudo bash -c ' + "'" + extract + cleanup + docker_run + "'\""])

parsed = ap.parse_args()
if parsed.action == 'list-machines':
    lmp = LibvirtMachineProvider()
    print(dumps({'machines': [m._to_dict() for m in lmp.get_machines()]}, indent=3))

elif parsed.action == 'migrate-machine':
    if not parsed.target:
        print('no target specified, creating leappto container package in current directory')
        # TODO: not really for now
    else:
        source = parsed.machine
        target = parsed.target

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

        print('! obtaining SSH keys')
        ssh = _get_ssh_config()
        print('! launching serializer')
        cpp = _get_tar_stream(machine_src.disks[0].host_path)
        #print('! ssh config:', ssh)
        print('! copying over')
        _copy_over(cpp, machine_dst.ip[0], ssh['target']).wait()
        print('! all done and well, provisioning ...')
        _process_in_target(machine_dst.ip[0], ssh['target']).wait()