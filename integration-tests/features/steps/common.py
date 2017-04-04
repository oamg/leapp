from behave import given, when, then, step
from hamcrest import assert_that, equal_to, not_none, greater_than

import json
import pathlib
import requests
import subprocess
import time

_TEST_DIR = pathlib.Path(__file__).parent.parent.parent
_REPO_DIR = _TEST_DIR.parent
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

@given("the local virtual machines")
def create_local_machines(context):
    vm_helper = context.vm_helper
    for row in context.table:
        ensure_fresh = (row["ensure_fresh"].lower() == "yes")
        vm_helper.ensure_local_vm(
            row["name"],
            row["definition"],
            destroy=ensure_fresh
        )


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

def _get_ip_addresses(source_host, target_host):
    leapp_output = _run_leapp("list-machines", "--shallow")
    machine_info = json.loads(leapp_output)
    source_ip = target_ip = None
    machines = machine_info["machines"]
    vm_count = len(machines)
    for machine in machines:
        if machine["hostname"] == source_host:
            source_ip = _get_leapp_ip(machine)
        if machine["hostname"] == target_host:
            target_ip = _get_leapp_ip(machine)
        if source_ip is not None and target_ip is not None:
            break
    return vm_count, source_ip, target_ip

@when("{source_vm} is redeployed to {target_vm} as a macrocontainer")
def redeploy_vm_as_macrocontainer(context, source_vm, target_vm):
    context.redeployment_source = source_vm
    context.redeployment_target = target_vm
    vm_helper = context.vm_helper
    source_host = vm_helper.get_hostname(source_vm)
    target_host = vm_helper.get_hostname(target_vm)
    _convert_vm_to_macrocontainer(source_host, target_host)
    vm_count, source_ip, target_ip = _get_ip_addresses(source_host, target_host)
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
