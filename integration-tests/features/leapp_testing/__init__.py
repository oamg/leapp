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
def _run_command(cmd, work_dir=None, ignore_errors=False, as_sudo=False):
    """Run non-interactive command and return stdout"""
    if as_sudo:
        cmd.insert(0, 'sudo')
        if 'SSH_AUTH_SOCK' in os.environ:
            cmd.insert(1, 'SSH_AUTH_SOCK=' + os.environ['SSH_AUTH_SOCK'])
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

    Set *keep_vms* to True to disable the automatic halting/destruction
    of VMs at the end of the test run.
    """

    def __init__(self, keep_vms=False):
        self.machines = {"localhost": "localhost"}
        self._resource_manager = contextlib.ExitStack()
        self._keep_vms = keep_vms

    def ensure_local_vm(self, name, definition, destroy=False, *, as_root=False):
        """Ensure a local VM exists based on the given definition

        *name*: name used to refer to the VM in scenario steps
        *definition*: directory name in integration-tests/vmdefs
        *destroy*: whether or not to destroy any existing VM
        """
        hostname = _VM_HOSTNAME_PREFIX + definition
        if hostname not in _VM_DEFS:
            raise ValueError("Unknown VM image: {}".format(definition))
        if destroy:
            self._vm_destroy(name, hostname, as_root=as_root)
        if self._vm_up(name, hostname, as_root=as_root) and not self._keep_vms:
            # Previously unknown VM, so register it for cleanup
            if destroy:
                self._resource_manager.callback(self._vm_destroy, name, hostname, as_root=as_root)
            else:
                self._resource_manager.callback(self._vm_halt, name, hostname, as_root=as_root)

    def get_hostname(self, name):
        """Return the expected hostname for the named machine"""
        return self.get_ip_address(name)

    def get_ip_address(self, name):
        """Return the expected IP address for the named machine"""
        return self._get_vm_ip_address(self.machines[name])

    def close(self):
        """Halt or destroy all created VMs"""
        self._resource_manager.close()

    def run_remote_command(self, name, *cmd, ignore_errors=False):
        """Run the given command on the named machine"""
        hostname = self.machines[name]
        return self._run_vagrant(hostname, "ssh", "--", *cmd,
                                 ignore_errors=ignore_errors)

    @staticmethod
    def _run_vagrant(hostname, *args, as_root=False, ignore_errors=False):
        # TODO: explore https://pypi.python.org/pypi/python-vagrant
        vm_dir = _VM_DEFS[hostname]
        if as_root and os.getuid() != 0:
            cmd = ["sudo", "vagrant"]
        else:
            cmd = ["vagrant"]
        cmd.extend(args)
        return _run_command(cmd, vm_dir, ignore_errors)

    @classmethod
    def _get_vm_ip_address(cls, hostname):
        if hostname == "localhost":
            return "127.0.0.1"
        vm_details = cls._run_vagrant(hostname, "ssh-config")
        for line in vm_details.splitlines():
            __, hostname_line, vm_ip = line.partition("HostName")
            if hostname_line:
                return vm_ip.strip()
        raise RuntimeError("No HostName entry found in 'vagrant ssh-config' output")

    def _vm_up(self, name, hostname, *, as_root=False):
        """Ensures given VM is running and runs Ansible provisioning playbook

        Return True if the VM was not previously registered, False otherwise.
        """
        up_result = self._run_vagrant(hostname, "up", as_root=as_root)
        print("Started {} VM instance".format(hostname))
        provision_result = self._run_vagrant(hostname, "provision", as_root=as_root)
        print("Provisioned {} VM instance".format(hostname))
        new_vm = name not in self.machines
        if new_vm:
            self.machines[name] = hostname
        return new_vm

    def _vm_halt(self, name, hostname, *, as_root=False):
        """Ensures given VM is suspended (if not already destroyed)"""
        try:
            hostname = self.machines.pop(name)
        except KeyError:
            pass
        result = self._run_vagrant(hostname, "halt", as_root=as_root, ignore_errors=True)
        print("Suspended {} VM instance".format(hostname))
        return result

    def _vm_destroy(self, name, hostname, *, as_root=False):
        """Ensures given VM is completely removes from the system"""
        try:
            hostname = self.machines.pop(name)
        except KeyError:
            pass
        result = self._run_vagrant(hostname, "destroy", as_root=as_root, ignore_errors=True)
        print("Destroyed {} VM instance".format(hostname))
        return result


##############################
# Leapp commands
##############################

_LEAPP_SRC_DIR = REPO_DIR / "src"
_PIPSI_BIN_DIR = REPO_DIR / "bin"
_PIPSI_LEAPP_TOOL_PATH = str(_PIPSI_BIN_DIR / "leapp-tool")

_SSH_USER = "vagrant"
_SSH_IDENTITY = str(REPO_DIR / "integration-tests/config/leappto_testing_key")
_SSH_PASSWORD = "vagrant"
_DEFAULT_LEAPP_USER = ['--user', _SSH_USER]
_DEFAULT_LEAPP_IDENTITY = ['--identity', _SSH_IDENTITY]
_DEFAULT_LEAPP_MIGRATE_USER = ['--target-user', _SSH_USER, '--source-user', _SSH_USER]
_DEFAULT_LEAPP_MIGRATE_IDENTITY = ['--target-identity', _SSH_IDENTITY, '--source-identity', _SSH_IDENTITY]

def install_client():
    """Install the CLI and its dependencies into a Python 2.7 environment"""
    py27 = shutil.which("python2.7")
    base_cmd = ["pipsi", "--bin-dir", str(_PIPSI_BIN_DIR)]
    if pathlib.Path(_PIPSI_LEAPP_TOOL_PATH).exists():
        # For some reason, `upgrade` returns 1 even though it appears to work
        # so we instead do a full uninstall/reinstall before the test run
        uninstall = base_cmd + ["uninstall", "--yes", "leappto"]
        _run_command(uninstall, work_dir=str(REPO_DIR), ignore_errors=False)
    install = base_cmd + ["install", "--python", py27, str(_LEAPP_SRC_DIR)]
    print(_run_command(install, work_dir=str(REPO_DIR), ignore_errors=False))
    # Ensure private SSH key is only readable by the current user
    os.chmod(_SSH_IDENTITY, 0o600)
    return _PIPSI_LEAPP_TOOL_PATH


class ClientHelper(object):
    """Test step helper to invoke the LeApp CLI

    Requires a VirtualMachineHelper instance
    """

    def __init__(self, vm_helper, leapp_tool_path):
        self._vm_helper = vm_helper
        self._leapp_tool_path = leapp_tool_path
        self.ensure_ssh_agent_is_running()
        self._add_default_ssh_key()

    def make_migration_command(self, source_vm, target_vm,
                               migration_opt=None,
                               force_create=False,
                               container_name=None):
        """Get command to recreate source VM as a macrocontainer on given target VM"""
        vm_helper = self._vm_helper
        source_host = vm_helper.get_ip_address(source_vm)
        target_host = vm_helper.get_ip_address(target_vm)
        return self._make_migration_command(
            source_host,
            target_host,
            migration_opt,
            force_create,
            container_name
        )

    def migrate_as_macrocontainer(self, source_vm, target_vm,
                                  migration_opt=None, force_create=False):
        """Recreate source VM as a macrocontainer on given target VM"""
        vm_helper = self._vm_helper
        source_host = vm_helper.get_ip_address(source_vm)
        target_host = vm_helper.get_ip_address(target_vm)
        return self._convert_vm_to_macrocontainer(
            source_host,
            target_host,
            migration_opt,
            force_create
        )

    def check_target(self, target_vm, time_limit=10):
        """Check viability of target VM and report currently unavailable names"""
        command_output = self.check_response_time(
            ["check-target", "-t", self._vm_helper.get_ip_address(target_vm)],
            time_limit,
            use_default_identity=True
        )
        return command_output.splitlines()


    def check_target_status(self, target_vm, time_limit=10):
        """Check services status of target VM and report results"""
        command_output = self.check_response_time(
            ["check-target", "--status", "-t", self._vm_helper.get_ip_address(target_vm)],
            time_limit,
            use_default_identity=True
        )
        return command_output.splitlines()


    def check_response_time(self, cmd_args, time_limit, *,
                            specify_default_user=False,
                            use_default_identity=False,
                            use_default_password=False,
                            as_sudo=False,
                            expect_failure=False):
        """Check given command completes within the specified time limit

        Returns the contents of stdout as a string.
        """
        is_migrate = 'migrate-machine' in cmd_args
        start = time.monotonic()
        if use_default_password:
            cmd_output = self._run_leapp_with_askpass(cmd_args, is_migrate=is_migrate)
        else:
            add_default_user = specify_default_user or use_default_identity
            try:
                cmd_output = self._run_leapp(cmd_args,
                                            add_default_user=add_default_user,
                                            add_default_identity=use_default_identity,
                                            is_migrate=is_migrate,
                                            as_sudo=as_sudo)
            except subprocess.CalledProcessError as exc:
                if not expect_failure:
                    raise
                cmd_output = exc.stdout
            else:
                if expect_failure:
                    raise AssertionError("Command succeeded unexpectedly")
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
        del os.environ["SSH_AUTH_SOCK"]
        del os.environ["SSH_AGENT_PID"]

    @classmethod
    def ensure_ssh_agent_is_running(cls):
        """Start ssh-agent if it isn't already running

        If the agent needed to be started, a shutdown callback is registered
        with the given ExitStack instance
        """
        try:
            agent_socket, agent_pid = cls._get_ssh_agent_details()
        except KeyError:
            agent_socket, agent_pid = cls._start_ssh_agent()
        return agent_socket, agent_pid

    @staticmethod
    def _add_default_ssh_key():
        """Add default testing key to ssh-agent"""
        cmd = ["ssh-add",  _SSH_IDENTITY]
        return _run_command(cmd)

    @staticmethod
    def remove_default_ssh_key():
        """Remove default testing key from ssh-agent"""
        cmd = ["ssh-add", "-d", _SSH_IDENTITY + ".pub"]
        return _run_command(cmd)

    @staticmethod
    def _requires_sudo(cmd_args):
        # These commands always require privileged access for nmap port scans
        needs_privileged_access = ("migrate-machine", "port-inspect")
        return any(cmd in cmd_args for cmd in needs_privileged_access)

    def _run_leapp(self, cmd_args, *,
                   add_default_user=False,
                   add_default_identity=False,
                   is_migrate=False,
                   as_sudo=False):
        as_sudo = as_sudo or self._requires_sudo(cmd_args)
        cmd = [self._leapp_tool_path]
        cmd.extend(cmd_args)
        if add_default_user:
            cmd.extend(_DEFAULT_LEAPP_MIGRATE_USER if is_migrate else _DEFAULT_LEAPP_USER)
        if add_default_identity:
            cmd.extend(_DEFAULT_LEAPP_MIGRATE_IDENTITY if is_migrate else _DEFAULT_LEAPP_IDENTITY)
        return _run_command(cmd, work_dir=str(REPO_DIR), as_sudo=as_sudo)

    def _run_leapp_with_askpass(self, cmd_args, is_migrate=False):
        # Helper specifically for --ask-pass testing with default credentials
        if os.getuid() != 0:
            err = "sshpass TTY emulation is incompatible with sudo credential caching"
            raise RuntimeError(err)
        cmd = ["sshpass", "-p"+_SSH_PASSWORD, self._leapp_tool_path]
        cmd.extend(cmd_args)
        cmd.extend(_DEFAULT_LEAPP_MIGRATE_USER if is_migrate else _DEFAULT_LEAPP_USER)
        cmd.append("--ask-pass")
        return _run_command(cmd, work_dir=str(REPO_DIR))

    @staticmethod
    def _make_migration_command(source_host, target_host, migration_opt,
                                force_create=False,
                                container_name=None):
        cmd_args = ["migrate-machine", "--tcp-port", "80:80"]
        if migration_opt == 'rsync':
            cmd_args.append('--use-rsync')
        if force_create:
            cmd_args.append('--force-create')
        if container_name is not None:
            cmd_args.extend(('--container-name', container_name))
        cmd_args.extend(("-t", target_host, source_host))
        return cmd_args

    def _convert_vm_to_macrocontainer(self, source_host, target_host,
                                      migration_opt, force_create):
        as_sudo = False
        cmd_args = self._make_migration_command(source_host, target_host,
                                               migration_opt, force_create)
        if '--use-rsync' in cmd_args:
            as_sudo = True
        result = self._run_leapp(cmd_args,
                                add_default_user=True,
                                add_default_identity=True,
                                is_migrate=True)
        msg = "Migrated {} as macrocontainer on {}"
        print(msg.format(source_host, target_host))
        return result


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
    def compare_migrated_response(cls, original_ip, migrated_ip, *,
                                    tcp_port, status, wait_for_target):
        """Compare a pre-migration app response with a post-migration response

        Expects an immediate response from the original IP, and allows for
        a delay before the migration target starts returning responses
        """
        # Get response from source VM
        original_url = "http://{}:{}".format(original_ip, tcp_port)
        original_response = cls.get_response(original_url)
        print("Response received from {}".format(original_url))
        original_status = original_response.status_code
        assert_that(original_status, equal_to(status), "Original status")
        # Get response from target VM
        migrated_url = "http://{}:{}".format(migrated_ip, tcp_port)
        migrated_response = cls.get_response(migrated_url, wait_for_target)
        print("Response received from {}".format(migrated_url))
        # Compare the responses
        assert_that(migrated_response.status_code,
                    equal_to(original_status),
                    "Post-migration status code didn't match original")
        original_data = original_response.text
        migrated_data = migrated_response.text
        assert_that(migrated_data, equal_to(original_data), "Same response")
