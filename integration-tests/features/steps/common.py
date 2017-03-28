from behave import given, when, then, step
from hamcrest import assert_that, equal_to, not_none, greater_than

import json
import pathlib
import requests
import subprocess
import time

_TEST_DIR = pathlib.Path(__file__).parent.parent.parent
_REPO_DIR = _TEST_DIR.parent
_VM_DEFS = {path.name: str(path) for path in (_TEST_DIR / "vmdefs").iterdir()}
_LEAPP_TOOL = str(_REPO_DIR / "leapp-tool.py")


##############################
# General utilities
##############################

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
# Local VM management
##############################

def _run_vagrant(vm_def, *args, ignore_errors=False):
    # TODO: explore https://pypi.python.org/pypi/python-vagrant
    #       That may require sudo-less access to vagrant
    vm_dir = _VM_DEFS[vm_def]
    cmd = ["vagrant"]
    cmd.extend(args)
    return _run_command(cmd, vm_dir, ignore_errors)

def _vm_up(vm_def):
    result = _run_vagrant(vm_def, "up")
    print("Started {} VM instance".format(vm_def))
    return result

def _vm_halt(vm_def):
    result = _run_vagrant(vm_def, "halt", ignore_errors=True)
    print("Suspended {} VM instance".format(vm_def))
    return result

def _vm_destroy(vm_def):
    result = _run_vagrant(vm_def, "destroy", ignore_errors=True)
    print("Destroyed {} VM instance".format(vm_def))
    return result


@given("the local virtual machines")
def create_local_machines(context):
    context.machines = machines = {}
    for row in context.table:
        vm_name = row["name"]
        vm_def = row["definition"]
        if vm_def not in _VM_DEFS:
            raise ValueError("Unknown VM image: {}".format(vm_def))
        ensure_fresh = (row["ensure_fresh"].lower() == "yes")
        if ensure_fresh:
            # TODO: Look at using "--provision" for fresh VMs
            #       Rather than a full destroy/recreate cycle
            #       Alternatively: add "reprovision" as a
            #       third state for the field
            _vm_destroy(vm_def)
        _vm_up(vm_def)
        if ensure_fresh:
            context.resource_manager.callback(_vm_destroy, vm_def)
        else:
            context.resource_manager.callback(_vm_halt, vm_def)
        machines[vm_name] = vm_def


##############################
# Leapp commands
##############################

def _run_leapp(*args):
    cmd = ["sudo", "/usr/bin/python2", _LEAPP_TOOL]
    cmd.extend(args)
    # Using _REPO_DIR as work_dir is a kludge to enable
    # the existing SSH kludge in leapp-tool itself,
    # which in turn relies on the tool only being used
    # with particular predefined Vagrant configurations
    return _run_command(cmd, work_dir=str(_REPO_DIR), ignore_errors=False)

def _convert_vm_to_macrocontainer(source_def, target_def):
    result = _run_leapp("migrate-machine", "-t", target_def, source_def)
    msg = "Redeployed {} as macrocontainer on {}"
    print(msg.format(source_def, target_def))
    return result

def _get_leapp_ip(machine):
    raw_ip = machine["ip"][0]
    if raw_ip.startswith("ipv4-"):
        return raw_ip[5:]
    return raw_ip

def _get_ip_addresses(source_def, target_def):
    leapp_output = _run_leapp("list-machines", "--shallow")
    machine_info = json.loads(leapp_output)
    source_ip = target_ip = None
    machines = machine_info["machines"]
    vm_count = len(machines)
    for machine in machines:
        # HACK: Require Vagrant config name to be used as hostname
        if machine["hostname"] == source_def:
            source_ip = _get_leapp_ip(machine)
        if machine["hostname"] == target_def:
            target_ip = _get_leapp_ip(machine)
        if source_ip is not None and target_ip is not None:
            break
    return vm_count, source_ip, target_ip

@when("{source_vm} is redeployed to {target_vm} as a macrocontainer")
def redeploy_vm_as_macrocontainer(context, source_vm, target_vm):
    context.redeployment_source = source_vm
    context.redeployment_target = target_vm
    machines = context.machines
    source_def = machines[source_vm]
    target_def = machines[target_vm]
    _convert_vm_to_macrocontainer(source_def, target_def)
    vm_count, source_ip, target_ip = _get_ip_addresses(source_def, target_def)
    assert_that(vm_count, greater_than(1), "At least 2 local VMs")
    assert_that(source_ip, not_none(), "Valid source IP")
    assert_that(target_ip, not_none(), "Valid target IP")
    context.redeployment_source_ip = source_ip
    context.redeployment_target_ip = target_ip


##############################
# Service status checking
##############################

def _get_target_response(redeployed_url, wait_for_target):
    deadline = time.monotonic()
    if wait_for_target is None:
        fail_msg = "No response from target"
    else:
        fail_msg = "No response from target within {} seconds".format(wait_for_target)
        deadline += wait_for_target
    while True:
        try:
            return requests.get(redeployed_url)
        except Exception:
            pass
        if time.monotonic() >= deadline:
            break
    raise AssertionError(fail_msg)

def _compare_responses(original_ip, redeployed_ip, *,
                       tcp_port, status, wait_for_target):
    # Get response from source VM
    original_url = "http://{}:{}".format(original_ip, tcp_port)
    original_response = requests.get(original_url)
    print("Response received from {}".format(original_url))
    original_status = original_response.status_code
    assert_that(original_status, equal_to(status), "Original status")
    # Get response from target VM
    redeployed_url = "http://{}:{}".format(redeployed_ip, tcp_port)
    redeployed_response = _get_target_response(redeployed_url, wait_for_target)
    print("Response received from {}".format(redeployed_url))
    # Compare the responses
    assert_that(redeployed_response.status_code, equal_to(original_status), "Redeployed status")
    original_data = original_response.text
    redeployed_data = redeployed_response.text
    assert_that(redeployed_data, equal_to(original_data), "Same response")

@then("the HTTP {status:d} response on port {tcp_port} should match within {wait_duration:g} seconds")
def check_http_responses_match(context, tcp_port, status, wait_duration):
    original_ip = context.redeployment_source_ip
    redeployed_ip = context.redeployment_target_ip
    assert_that(original_ip, not_none(), "Valid original IP")
    assert_that(redeployed_ip, not_none(), "Valid redeployment IP")
    _compare_responses(
        original_ip, redeployed_ip,
        tcp_port=tcp_port,
        status=status,
        wait_for_target=wait_duration
    )
