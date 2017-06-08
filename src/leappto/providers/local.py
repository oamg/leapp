from leappto.driver import LocalDriver
from leappto.providers.ssh import SSHMachine
from leappto import MachineType, Machine

class LocalMachine(SSHMachine):
    def __init__(self, shallow_scan=True):
        super(LocalMachine, self).__init__(LocalDriver())
        self._type = MachineType.Local

