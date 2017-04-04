from behave import given, when, then, step
from hamcrest import assert_that, equal_to, not_none, greater_than

import json
import requests
import time


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

@when("{source_vm} is redeployed to {target_vm} as a macrocontainer")
def redeploy_vm_as_macrocontainer(context, source_vm, target_vm):
    context.redeployment_source = source_vm
    context.redeployment_target = target_vm
    migration_helper = context.migration_helper
    result = migration_helper.redeploy_as_macrocontainer(source_vm, target_vm)
    assert_that(result.local_vm_count, greater_than(1), "At least 2 local VMs")
    assert_that(result.source_ip, not_none(), "Valid source IP")
    assert_that(result.target_ip, not_none(), "Valid target IP")
    context.redeployment_source_ip = result.source_ip
    context.redeployment_target_ip = result.target_ip


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
