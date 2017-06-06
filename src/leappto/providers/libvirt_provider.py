import errno
import json
import libvirt
import os
import shlex
import socket
from io import BytesIO
from subprocess import check_output
from xml.etree import ElementTree as ET

from leappto import AbstractMachineProvider, MachineType, Machine, Disk, \
        Package, OperatingSystem, Installation
from leappto.driver.ssh import VagrantSSHDriver
from leappto.providers.ssh_provider import inspect_machine

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

            vagrant_driver = VagrantSSHDriver(domain.name())
            ips, hostname, inst = inspect_machine(vagrant_driver, self._shallow_scan)

            storage = __get_storage(root.findall("devices/disk[@device='disk']"))

            return LibvirtMachine(domain.UUIDString(), hostname,
                                  ips, os_type.get('arch'), vt, storage,
                                  next(root.find('name').itertext()), inst, self)

        domains = self.connection.listAllDomains(0)
        return [__domain_info(dom) for dom in domains if dom.isActive()]
