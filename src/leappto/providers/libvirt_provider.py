import errno
import json
import libvirt
import os
import shlex
import socket
from io import BytesIO
from subprocess import check_output
from xml.etree import ElementTree as ET

from paramiko import AutoAddPolicy, SSHClient, SSHConfig

from leappto import AbstractMachineProvider, MachineType, Machine, Disk, \
        Package, OperatingSystem, Installation


class LibvirtMachine(Machine):
    # TODO: Libvirt Python API doesn't seem to expose 
    # virDomainSuspend and virDomainResume so use Virsh
    # for the time being
    def suspend(self):
        return check_output(['sudo', 'virsh', 'suspend', self.id])

    def resume(self):
        return check_output(['sudo', 'virsh', 'resume', self.id])


class LibvirtMachineProvider(AbstractMachineProvider):
    def __init__(self, shallow_scan=True):
        self._connection = libvirt.open('qemu:///system')
        self._shallow_scan = shallow_scan
        # Stupid `libvirt` cannot carry out certain *read only* operations while
        # being in read-only mode so just use `open` and fix this later by enumerating
        # networks, checking the MAC of the domain and correlating this against DHCP leases
        # self._connection = libvirt.openReadOnly('qemu:///system')

    @property
    def connection(self):
        return self._connection

    def __del__(self):
        if self._connection:
            self._connection.close()
        del self._connection

    def get_machines(self):
        """
        Get `Machine` description for each active machine

        :return: List[Machine], List of machines running on the system
        """

        def __good_ip(ip):
            """
            Check whether the given IP address is considered good

            :param ip: str, ip address to check
            """
            if ip in {'127.0.0.1', '::1'}:
                return False
            return True

        def __get_ip_addresses(domain):
            """

            :param domain: libvirt.virDomain, Domain for which to fetch the information
            """
            ifaces = domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
            for (name, val) in ifaces.items():
                if val['addrs']:
                    for ipaddr in val['addrs']:
                        if not __good_ip(ipaddr['addr']):
                            continue
                        yield ipaddr['addr']

        def __get_attribute(elem, attr):
            """
            Get attribute if we have valid element

            :param elem: xml.etree.ElementTree.Element, element
            :param attr: str, attribute name
            :return: str, attribute value
            """
            if elem is not None:
                return elem.get(attr)

        def __get_storage(disks):
            """
            Get `Disk` objects from XML

            :param disks: List[xml.etree.ElementTree.Element], disk xml elements
            :return: List[Disk], list of Disks
            """
            storage = []
            for disk in disks:
                type_ = disk.get('type')
                backing_file = __get_attribute(disk.find('source[@file]'), 'file')
                driver_type = __get_attribute(disk.find('driver[@type]'), 'type')
                device = __get_attribute(disk.find('target[@dev]'), 'dev')
                storage.append(Disk(type_, backing_file, device, driver_type))
            return storage

        def __get_value(elem):
            """

            :param elem: List[xml.etree.ElementTree.Element], xml tree element
            :return:
            """
            if elem is not None:
                return next(elem.itertext())
            else:
                return ''

        def __virt_inspector_supports_shallow():
            """
            :return: True if virt-inspector supports --no-applications and --no-icon
            """
            inspector_version = check_output(['virt-inspector', '-V'])
            major, minor, _ = inspector_version.split(' ')[1].split('.', 2)
            return (major, minor) >= ('1', '34')


        def __inspect_os(domain_name):
            """

            :param domain_name: str, which domain to inspect
            :return:
            """
            cmd = ['sudo', 'virt-inspector', '-d', domain_name]
            if __virt_inspector_supports_shallow():
                cmd.append('--no-icon')
                if self._shallow_scan:
                    cmd.append('--no-applications')
            os_data = check_output(cmd)
            root = ET.fromstring(os_data)
            packages = []

            distro = __get_value(root.find('operatingsystem/distro'))
            major = __get_value(root.find('operatingsystem/major_version'))
            minor = __get_value(root.find('operatingsystem/minor_version'))
            hostname = __get_value(root.find('operatingsystem/hostname'))

            for package in root.findall('operatingsystem/applications/application'):
                name = __get_value(package.find('name'))
                epoch = __get_value(package.find('epoch'))
                version = __get_value(package.find('version'))
                arch = __get_value(package.find('arch'))
                release = __get_value(package.find('release'))
                package = Package(name, '{e}:{v}-{r}-{a}'.format(e=epoch or 0, v=version, a=arch, r=release))
                packages.append(package)

            return (hostname, Installation(OperatingSystem(distro, '{}.{}'.format(major, minor)), packages))

        def __get_vagrant_data_path_from_domain(domain_name):
            index_path = os.path.join(os.environ['HOME'], '.vagrant.d/data/machine-index/index')
            index = json.load(open(index_path, 'r'))
            for ident, machine in index['machines'].iteritems():
                path_name = os.path.basename(machine['vagrantfile_path'])
                vagrant_name = machine.get('name', 'default')
                if domain_name == path_name + '_' + vagrant_name:
                    return machine['local_data_path']
            return None

        def __get_vagrant_ssh_args_from_domain(domain_name):
            path = __get_vagrant_data_path_from_domain(domain_name)
            path = os.path.join(path, 'provisioners/ansible/inventory/vagrant_ansible_inventory')
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line[0] in (';', '#'):
                        continue
                    return __parse_ansible_inventory_data(line)
            return None

        def __parse_ansible_inventory_data(line):
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

        def __get_vagrant_ssh_client_for_domain(domain_name):
            args = __get_vagrant_ssh_args_from_domain(domain_name)
            if args:
                client = SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(AutoAddPolicy())
                client.connect(args.pop('hostname'), **args)
                return client
            return None

        def __get_ssh_info(domain_name):
            client = __get_vagrant_ssh_client_for_domain(domain_name)
            if not client:
                return None
            cmd = """python -c 'import platform; print chr(0xa).join(platform.linux_distribution()[:2])'"""
            _, output, _ = client.exec_command(cmd)
            distro, version = output.read().strip().replace('\r', '').split('\n', 1)
            cmd = """python -c 'import socket; print socket.gethostname()'"""
            _, output, _ = client.exec_command(cmd)
            hostname = output.read().strip()
            cmd = "/sbin/ip -4 -o addr list | grep -E 'e(th|ns)' | sed 's/.*inet \\([0-9\\.]\\+\\)\\/.*$/\\1/g'\n"
            _, output, stderr = client.exec_command(cmd)
            ips = [i.strip() for i in output.read().split('\n') if i.strip()]
            return (ips, hostname, Installation(OperatingSystem(distro, version), []))


        def __get_info_shallow(domain, force_ssh=False):
            result = None
            if not force_ssh:
                domxml = ET.fromstring(domain.XMLDesc(0))
                channel = domxml.find('devices/channel/source')
                if channel is not None:
                    result = __get_agent_info(channel)
                if not result and __virt_inspector_supports_shallow():
                    result = (list(__get_ip_addresses(domain)),) + __inspect_os(domain.name())
            if not result:
                result = __get_ssh_info(domain.name())
            return result

        def __get_agent_info(channel):
            result = -1
            if channel is not None:
                path = channel.attrib['path']
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.setblocking(0)
                result = sock.connect_ex(path)

            def _consume(flush=False):
                while True:
                    try:
                        data = sock.recv(2 ** 16)
                        if not flush:
                            yield data
                    except socket.error as err:
                        if err.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                            raise
                        if flush and err.errno == errno.EWOULDBLOCK:
                            break
            needed = {'os-info': None, 'fqdn': None,
                      'network-interfaces': None}
            if result == 0:
                _consume(flush=True)
                sock.sendall('{"__name__": "refresh", "apiVersion": 3}\n'
                             '{"__name__": "api-version", "apiVersion": 3}\n')
                linebuffer = ""
                for buf in _consume():
                    linebuffer += buf
                    try:
                        line, linebuffer = linebuffer.split('\n', 1)
                    except ValueError:
                        break
                    data = json.loads(line)
                    msg = data.pop('__name__')
                    if msg in needed:
                        needed[msg] = data
                    if all(needed.values()):
                        break
                intfs = needed['network-interfaces']
                ips = [a for i in intfs['interfaces'] for a in i['inet']]
                fqdn = needed['fqdn']['fqdn']
                distro = needed['os-info']['distribution']
                version = needed['os-info']['version']
                return (ips, fqdn, Installation(OperatingSystem(distro, version), []))
            return None


        def __domain_info(domain):
            """
            Create `Machine` description out of `virDomain` object

            :param domain: libvirt.virDomain, Domain for which to fetch the information
            """
            desc = domain.XMLDesc()
            root = ET.fromstring(desc)

            os_type = root.find('os/type')
            typ = next(os_type.itertext())
            vt = MachineType.Default

            if 'kvm' in root.get('type'):
                vt |= MachineType.Kvm
            if 'hvm' in typ:
                vt |= MachineType.Hvm

            '''
            Too much log spew and doesn't work

            try:
                # This can fail on a number of occasions:
                # 1) Theres no guest agent installed
                # 2) The connection doesn't support the call
                hostname = domain.hostname()
            except libvirt.libvirtError:
                hostname = None
            '''

            if self._shallow_scan:
                ips, hostname, inst = __get_info_shallow(domain)
            else:
                hostname, inst = __inspect_os(domain.name())
                ips = list(__get_ip_addresses(domain))

            storage = __get_storage(root.findall("devices/disk[@device='disk']"))

            return LibvirtMachine(domain.UUIDString(), hostname,
                                  ips, os_type.get('arch'), vt, storage,
                                  next(root.find('name').itertext()), inst, self)

        domains = self.connection.listAllDomains(0)
        return [__domain_info(dom) for dom in domains if dom.isActive()]
