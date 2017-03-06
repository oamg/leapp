import libvirt
from leappto import AbstractMachineProvider, MachineType, Machine, Disk, Package, OperatingSystem, Installation
from xml.etree import ElementTree as ET
from subprocess import check_output


class LibvirtMachineProvider(AbstractMachineProvider):
    def __init__(self):
        self._connection = libvirt.open('qemu:///system')
        # Stupid `libvirt` cannot carry out certain *read only* operations while
        # being in read-only mode so just use `open` and fix this later by enumerating
        # networks, checking the MAC of the domain and correlating this against DHCP leases
        #self._connection = libvirt.openReadOnly('qemu:///system')

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
                        if ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                            yield 'ipv4-' + ipaddr['addr']
                        elif ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV6:
                            yield 'ipv6-' + ipaddr['addr']

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
            os_data = check_output(['virt-inspector', '-d', domain_name])
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

            hostname, inst = __inspect_os(domain.name())

            storage = __get_storage(root.findall("devices/disk[@device='disk']"))

            return Machine(domain.UUIDString(), hostname,
                           list(__get_ip_addresses(domain)),
                           os_type.get('arch'), vt, storage,
                           next(root.find('name').itertext()), inst, self)

        domains = self.connection.listAllDomains(0)
        return [__domain_info(dom) for dom in domains if dom.isActive()]
