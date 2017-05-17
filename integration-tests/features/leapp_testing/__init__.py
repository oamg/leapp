import contextlib
import json
import os
import pathlib
import shutil
import subprocess
import time

from attr import attributes, attrib
from hamcrest import assert_that, equal_to, less_than_or_equal_to

import requests

##############################
# General utilities
##############################
TEST_DIR = pathlib.Path(__file__).parent.parent.parent
REPO_DIR = TEST_DIR.parent

# Command execution helper
<<<<<<< HEAD
def _run_command(cmd, work_dir=None, ignore_errors=False):
    """Run non-interactive command and return stdout"""
=======
def _run_command(cmd, work_dir=None, ignore_errors=False, as_sudo=False):
    if as_sudo and isinstance(cmd, list):
        cmd.insert(0, 'sudo')
>>>>>>> master
    if work_dir is not None:
        print("  Running {} in {}".format(cmd, work_dir))
    else:
        print("  Running", cmd)
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
# Local VM management
##############################

_VM_HOSTNAME_PREFIX = "leapp-tests-"
_VM_DEFS = {
    _VM_HOSTNAME_PREFIX + path.name: str(path)
        for path in (TEST_DIR / "vmdefs").iterdir()
}

class VirtualMachineHelper(object):
    """Test step helper to launch and manage VMs

    Currently based specifically on local Vagrant VMs
    """

    def __init__(self):
        self.machines = {}
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
            self._vm_destroy(hostname)
        self._vm_up(name, hostname)
        if destroy:
            self._resource_manager.callback(self._vm_destroy, name)
        else:
            self._resource_manager.callback(self._vm_halt, name)

    def get_hostname(self, name):
        """Return the expected hostname for the named machine"""
        return self.machines[name]

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

    def _vm_up(self, name, hostname):
        result = self._run_vagrant(hostname, "up", "--provision")
        print("Started {} VM instance".format(hostname))
        self.machines[name] = hostname
        return result

    def _vm_halt(self, name):
        hostname = self.machines.pop(name)
        result = self._run_vagrant(hostname, "halt", ignore_errors=True)
        print("Suspended {} VM instance".format(hostname))
        return result

    def _vm_destroy(self, name):
        hostname = self.machines.pop(name)
        result = self._run_vagrant(hostname, "destroy", ignore_errors=True)
        print("Destroyed {} VM instance".format(hostname))
        return result


##############################
# Leapp commands
##############################

_LEAPP_SRC_DIR = REPO_DIR / "src"
_LEAPP_BIN_DIR = REPO_DIR / "bin"
_LEAPP_TOOL = str(_LEAPP_BIN_DIR / "leapp-tool")

_SSH_USER = "vagrant"
_SSH_IDENTITY = str(REPO_DIR / "integration-tests/config/leappto_testing_key")
_SSH_PASSWORD = "vagrant"
_DEFAULT_LEAPP_USER = ['--user', _SSH_USER]
_DEFAULT_LEAPP_IDENTITY = ['--identity', _SSH_IDENTITY]

def install_client():
    """Install the CLI and its dependencies into a Python 2.7 environment"""
    py27 = shutil.which("python2.7")
    base_cmd = ["pipsi", "--bin-dir", str(_LEAPP_BIN_DIR)]
    if pathlib.Path(_LEAPP_TOOL).exists():
        # For some reason, `upgrade` returns 1 even though it appears to work
        # so we instead do a full uninstall/reinstall before the test run
        uninstall = base_cmd + ["uninstall", "--yes", "leappto"]
        _run_command(uninstall, work_dir=str(REPO_DIR), ignore_errors=False)
    install = base_cmd + ["install", "--python", py27, str(_LEAPP_SRC_DIR)]
    print(_run_command(install, work_dir=str(REPO_DIR), ignore_errors=False))
    # Ensure private SSH key is only readable by the current user
    os.chmod(_SSH_IDENTITY, 0o600)

@attributes
class MigrationInfo(object):
    """Details of local hosts involved in an app migration command

    *local_vm_count*: Total number of local VMs found during migration
    *source_ip*: host accessible IP address found for source VM
    *target_ip*: host accessible IP address found for target VM
    """
    local_vm_count = attrib()
    source_ip = attrib()
    target_ip = attrib()

    @classmethod
    def from_vm_list(cls, machines, source_host, target_host):
        """Build a result given a local VM listing and migration hostnames"""
        vm_count = len(machines)
        source_ip = target_ip = None
        for machine in machines:
            if machine["hostname"] == source_host:
                source_ip = machine["ip"][0]
            if machine["hostname"] == target_host:
                target_ip = machine["ip"][0]
            if source_ip is not None and target_ip is not None:
                break
        return cls(vm_count, source_ip, target_ip)


class ClientHelper(object):
    """Test step helper to invoke the LeApp CLI

    Requires a VirtualMachineHelper instance
    """

    def __init__(self, vm_helper):
        self._vm_helper = vm_helper

    def redeploy_as_macrocontainer(self, source_vm, target_vm):
        """Recreate source VM as a macrocontainer on given target VM"""
        vm_helper = self._vm_helper
        source_host = vm_helper.get_hostname(source_vm)
        target_host = vm_helper.get_hostname(target_vm)
        self._convert_vm_to_macrocontainer(source_host, target_host)
        return self._get_migration_host_info(source_host, target_host)

    def check_response_time(self, cmd_args, time_limit, *,
                            specify_default_user=False,
                            use_default_identity=False,
                            use_default_password=False,
                            as_sudo=False):
        """Check given command completes within the specified time limit

        Returns the contents of stdout as a string.
        """
        start = time.monotonic()
        if use_default_password:
            cmd_output = self._run_leapp_with_askpass(cmd_args)
        else:
            add_default_user = specify_default_user or use_default_identity
            cmd_output = self._run_leapp(cmd_args,
                                         add_default_user=add_default_user,
                                         add_default_identity=use_default_identity,
                                         as_sudo=as_sudo)
        response_time = time.monotonic() - start
        assert_that(response_time, less_than_or_equal_to(time_limit))
        return cmd_output

    @staticmethod
    def _get_ssh_agent_details():
        return os.environ["SSH_AUTH_SOCK"], os.environ["SSH_AGENT_PID"]

    @staticmethod
    def _start_ssh_agent():
        agent_details = _run_command(["ssh-agent", "-c"]).splitlines()
        agent_socket = agent_details[0].split()[2].rstrip(";")
        agent_pid = agent_details[1].split()[2].rstrip(";")
        os.environ["SSH_AUTH_SOCK"] = agent_socket
        os.environ["SSH_AGENT_PID"] = agent_pid
        return agent_socket, agent_pid

    @staticmethod
    def _stop_ssh_agent():
        _run_command(["ssh-agent", "-k"])

    @classmethod
    def ensure_ssh_agent_is_running(cls, cleanup_stack):
        """Start ssh-agent if it isn't already running

        If the agent needed to be started, a shutdown callback is registered
        with the given ExitStack instance
        """
        try:
            agent_socket, agent_pid = cls._get_ssh_agent_details()
        except KeyError:
            agent_socket, agent_pid = cls._start_ssh_agent()
            cleanup_stack.callback(cls._stop_ssh_agent)
        return agent_socket, agent_pid

    @classmethod
    def add_default_ssh_key(cls, cleanup_stack):
        """Add default testing key to ssh-agent

        A key removal callback is registered with the given ExitStack instance
        """
        cmd = ["ssh-add",  _SSH_IDENTITY]
        result = _run_command(cmd)
        cleanup_stack.callback(cls._remove_default_ssh_key)
        return result

    @staticmethod
    def _remove_default_ssh_key():
        """Remove default testing key from ssh-agent"""
        cmd = ["ssh-add", "-d", _SSH_IDENTITY + ".pub"]
        return _run_command(cmd)

    @staticmethod
    def _run_leapp(cmd_args, *,
                   add_default_user=False,
                   add_default_identity=False,
                   as_sudo=False):
        cmd = [_LEAPP_TOOL]
        cmd.extend(cmd_args)
        if add_default_user:
            cmd.extend(_DEFAULT_LEAPP_USER)
        if add_default_identity:
            cmd.extend(_DEFAULT_LEAPP_IDENTITY)
<<<<<<< HEAD
        return _run_command(cmd, work_dir=str(_LEAPP_BIN_DIR))

    @staticmethod
    def _run_leapp_with_askpass(cmd_args):
        # Helper specifically for --ask-pass testing with default credentials
        if os.getuid() != 0:
            err = "sshpass TTY emulation is incompatible with sudo credential caching"
            raise RuntimeError(err)
        cmd = ["sshpass", "-p"+_SSH_PASSWORD, _LEAPP_TOOL]
        cmd.extend(cmd_args)
        cmd.extend(("--user", _SSH_USER, "--ask-pass"))
        return _run_command(cmd, work_dir=str(_LEAPP_BIN_DIR))
=======
        return _run_command(cmd, work_dir=str(_LEAPP_BIN_DIR), ignore_errors=False, as_sudo=as_sudo)
>>>>>>> master

    @classmethod
    def _convert_vm_to_macrocontainer(cls, source_host, target_host):
        cmd_args = ["migrate-machine"]
        cmd_args.extend(["-t", target_host, source_host])
        result = cls._run_leapp(cmd_args,
                                add_default_user=True,
                                add_default_identity=True)
        msg = "Redeployed {} as macrocontainer on {}"
        print(msg.format(source_host, target_host))
        return result

    @classmethod
    def _get_migration_host_info(cls, source_host, target_host):
        leapp_output = cls._run_leapp(["list-machines", "--shallow"])
        machines = json.loads(leapp_output)["machines"]
        return MigrationInfo.from_vm_list(machines, source_host, target_host)


##############################
# Service status checking
##############################

class RequestsHelper(object):
    """Test step helper to check HTTP responses"""

    @classmethod
    def get_response(cls, service_url, wait_for_connection=None):
        """Get HTTP response from given service URL

        Responses are returned as requests.Response objects

        *service_url*: the service URL to query
        *wait_for_connection*: number of seconds to wait for a HTTP connection
                               to the service. `None` indicates that a response
                               is expected immediately.
        """
        deadline = time.monotonic()
        if wait_for_connection is None:
            fail_msg = "No response from {}".format(service_url)
        else:
            fail_msg = "No response from {} within {} seconds".format(
                service_url,
                wait_for_connection
            )
            deadline += wait_for_connection
        while True:
            try:
                return requests.get(service_url)
            except Exception:
                pass
            if time.monotonic() >= deadline:
                break
        raise AssertionError(fail_msg)

    @classmethod
    def get_responses(cls, urls_to_check):
        """Check responses from multiple given URLs

        Each URL can be either a string (which will be expected to return
        a response immediately), or else a (service_url, wait_for_connection)
        pair, which is interpreted as described for `get_response()`.

        Response are returned as a dictionary mapping from the service URLs
        to requests.Response objects.
        """
        # TODO: Use concurrent.futures to check the given URLs in parallel
        responses = {}
        for url_to_check in urls_to_check:
            if isinstance(url_to_check, tuple):
                url_to_check, wait_for_connection = url_to_check
            else:
                wait_for_connection = None
            responses[url_to_check] = cls.get_response(url_to_check,
                                                       wait_for_connection)
        return responses

    @classmethod
    def compare_redeployed_response(cls, original_ip, redeployed_ip, *,
                                    tcp_port, status, wait_for_target):
        """Compare a pre-migration app response with a redeployed response

        Expects an immediate response from the original IP, and allows for
        a delay before the redeployment target starts returning responses
        """
        # Get response from source VM
        original_url = "http://{}:{}".format(original_ip, tcp_port)
        original_response = cls.get_response(original_url)
        print("Response received from {}".format(original_url))
        original_status = original_response.status_code
        assert_that(original_status, equal_to(status), "Original status")
        # Get response from target VM
        redeployed_url = "http://{}:{}".format(redeployed_ip, tcp_port)
        redeployed_response = cls.get_response(redeployed_url, wait_for_target)
        print("Response received from {}".format(redeployed_url))
        # Compare the responses
        assert_that(redeployed_response.status_code, equal_to(original_status), "Redeployed status")
        original_data = original_response.text
        redeployed_data = redeployed_response.text
        assert_that(redeployed_data, equal_to(original_data), "Same response")
