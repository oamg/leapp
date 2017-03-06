"""

"""
from enum import IntEnum


class MachineType(IntEnum):
    Default = 0
    Kvm = 1
    Hvm = 2


class DiskType(IntEnum):
    Default = 0
    Disk = 1
    Cdrom = 2


class StorageFormat(IntEnum):
    Default = 0
    QCOW2 = 1
    RAW = 2


class NameVersion:
    _NAME = 'NameVersion'

    def __init__(self, name, version):
        self._name = name
        self._version = version

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    def _to_dict(self):
        return {'name': self.name, 'version': self.version}

    def __repr__(self):
        return '<{_name} name={name}, version={version}>'.format(_name=self._NAME, name=self.name, version=self.version)


class OperatingSystem(NameVersion):
    _NAME = 'OperatingSystem'


class Package(NameVersion):
    _NAME = 'Package'


class Installation:
    def __init__(self, os, packages):
        self._os = os
        self._packages = packages

    @property
    def os(self):
        return self._os

    @property
    def packages(self):
        return self._packages

    def _to_dict(self):
        return {'os': self.os._to_dict(), 'packages': [pkg._to_dict() for pkg in self.packages]}

    def __repr__(self):
        return '<Installation os={os}, packages={packages}>'.format(**self._to_dict())


class Disk:
    def __init__(self, dt, host_path, device, sf):
        self._disk_type = dt
        self._host_path = host_path
        self._device = device
        self._storage_format = sf

    @property
    def disk_type(self):
        return self._disk_type

    @property
    def host_path(self):
        return self._host_path

    @property
    def device(self):
        return self._device

    @property
    def storage_format(self):
        return self._storage_format

    def _to_dict(self):
        return {'type': self.disk_type, 'format': self.storage_format,
                'host_path': self.host_path, 'device': self.device}

    def __repr__(self):
        arg = {'type': self.disk_type, 'format': self.storage_format,
               'host_path': self.host_path, 'device': self.device}
        msg = '<Disk type={type}, format={format}, path={host_path}, device={device}>'
        return msg.format(**arg)


class Machine:

    _NAME='Machine'

    def __init__(self, id_, hostname, ip, arch, type_, disks, name, installation, provider):
        self._id = id_
        self._hostname = hostname
        self._ip = ip
        self._arch = arch
        self._type = type_
        self._disks = disks
        self._provider = provider
        self._name = name
        self._installation = installation

    @property
    def id(self):
        return self._id

    @property
    def hostname(self):
        return self._hostname

    @property
    def ip(self):
        return self._ip

    @property
    def arch(self):
        return self._arch

    @property
    def type(self):
        return self._type

    @property
    def provider(self):
        return self._provider

    @property
    def name(self):
        return self._name

    @property
    def disks(self):
        return self._disks

    @property
    def installation(self):
        return self._installation

    def _to_dict(self):
        return {'id': self.id, 'hostname': self.hostname, 'ip': self.ip,
               'arch': self.arch, 'type': self.type,
               'disks': [d._to_dict() for d in self.disks], 'name': self.name,
               'os': self.installation._to_dict()}

    def __repr__(self):
        arg = {'id': self.id, 'hostname': self.hostname, 'ip': self.ip,
               'arch': self.arch, 'type': self.type, '_name': self._NAME,
               'disks': repr(self.disks), 'n': self.name}
        msg = '<{_name} id={id}, name={n}, hostname={hostname}, ip={ip}, arch={arch}, type={type}, disks={disks}>'
        return msg.format(**arg)


class AbstractMachineProvider:
    def get_machines(self):
        """

        :return: List[AbstractMachine], list of all virtual machines
        """
        raise NotImplementedError
