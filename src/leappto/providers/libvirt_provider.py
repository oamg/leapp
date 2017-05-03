import libvirt
from leappto import AbstractMachineProvider, MachineType, Machine, Disk, Package, OperatingSystem, Installation
from xml.etree import ElementTree as ET
from subprocess import check_output
import socket
import errno
import json

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

        def __inspect_os(domain_name):
            """

            :param domain_name: str, which domain to inspect
            :return:
            """
            inspector_version = check_output(['virt-inspector', '-V'])
            major, minor, _ = inspector_version.split(' ')[1].split('.', 2)
            # Vagrant always uses qemu:///system, so for now, we always run
            # virt-inspector as root, rather than as the current user
            cmd = ['sudo', 'virt-inspector', '-d', domain_name]
            if int(minor) >= 34 or int(major) > 1:
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

        def __get_agent_info(domain):
            domxml = ET.fromstring(domain.XMLDesc(0))
            channel = domxml.find('devices/channel/source')
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
            return (list(__get_ip_addresses(domain)),) + __inspect_os(domain.name())


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
                ips, hostname, inst = __get_agent_info(domain)
            else:
                hostname, inst = __inspect_os(domain.name())
                ips = list(__get_ip_addresses(domain))

            storage = __get_storage(root.findall("devices/disk[@device='disk']"))

            return Machine(domain.UUIDString(), hostname,
                           ips, os_type.get('arch'), vt, storage,
                           next(root.find('name').itertext()), inst, self)

        domains = self.connection.listAllDomains(0)
        return [__domain_info(dom) for dom in domains if dom.isActive()]
