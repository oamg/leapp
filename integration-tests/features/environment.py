import contextlib
import pathlib
import subprocess

##############################
# General utilities
##############################
_TEST_DIR = pathlib.Path(__file__).parent.parent
_REPO_DIR = _TEST_DIR.parent

# Command execution helper
def _run_command(cmd, work_dir, ignore_errors):
    print("  Running {} in {}".format(cmd, work_dir))
    output = None
    try:
        output = subprocess.check_output(
            cmd, cwd=work_dir, stderr=subprocess.PIPE
        ).decode()
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        if not ignore_errors:
            print("=== stdout for failed command ===")
            print(output)
            print("=== stderr for failed command ===")
            print(exc.stderr.decode())
            raise
    return output

##############################
# Test step helpers
##############################
_VM_HOSTNAME_PREFIX = "leapp-tests-"
_VM_DEFS = {
    _VM_HOSTNAME_PREFIX + path.name: str(path)
        for path in (_TEST_DIR / "vmdefs").iterdir()
}

class VirtualMachineHelper(object):
    """Test step helper to launch and manage VMs

    Currently based specifically on local Vagrant VMs
    """

    def __init__(self):
        self._machines = {}
        self._resource_manager = contextlib.ExitStack()

    def ensure_local_vm(self, name, definition, destroy=False):
        """Ensure a local VM exists based on the given definition

        *name*: name used to refer to the VM in scenario steps
        *definition*: directory name in integration-tests/vmdefs
        *destroy*: whether or not to destroy any existing VM
        """
        hostname = _VM_HOSTNAME_PREFIX + definition
        if hostname not in _VM_DEFS:
            raise ValueError("Unknown VM image: {}".format(definition))
        if destroy:
            # TODO: Look at using "--provision" for fresh VMs
            #       rather than a full destroy/recreate cycle
            #       Alternatively: add "reprovision" as a
            #       separate option for machine creation or
            #       even make it the default for `destroy=False`
            self._vm_destroy(hostname)
        self._vm_up(hostname)
        if destroy:
            self._resource_manager.callback(self._vm_destroy, hostname)
        else:
            self._resource_manager.callback(self._vm_halt, hostname)
        self._machines[name] = hostname

    def get_hostname(self, name):
        """Return the expected hostname for the named machine"""
        return self._machines[name]

    def close(self):
        """Halt or destroy all created VMs"""
        self._resource_manager.close()

    @staticmethod
    def _run_vagrant(hostname, *args, ignore_errors=False):
        # TODO: explore https://pypi.python.org/pypi/python-vagrant
        vm_dir = _VM_DEFS[hostname]
        cmd = ["vagrant"]
        cmd.extend(args)
        return _run_command(cmd, vm_dir, ignore_errors)

    @classmethod
    def _vm_up(cls, hostname):
        result = cls._run_vagrant(hostname, "up")
        print("Started {} VM instance".format(hostname))
        return result

    @classmethod
    def _vm_halt(cls, hostname):
        result = cls._run_vagrant(hostname, "halt", ignore_errors=True)
        print("Suspended {} VM instance".format(hostname))
        return result

    @classmethod
    def _vm_destroy(cls, hostname):
        result = cls._run_vagrant(hostname, "destroy", ignore_errors=True)
        print("Destroyed {} VM instance".format(hostname))
        return result

##############################
# Test execution hooks
##############################

def before_all(context):
    # Some steps require sudo, so for convenience in interactive use,
    # we ensure we prompt for elevated permissions immediately,
    # rather than potentially halting midway through a test
    subprocess.check_output(["sudo", "echo", "Elevated permissions needed"])

def before_scenario(context, scenario):
    context.resource_manager = resource_manager = contextlib.ExitStack()
    context.vm_helper = vm_helper = VirtualMachineHelper()
    resource_manager.callback(vm_helper.close)

def after_scenario(context, scenario):
    context.resource_manager.close()
