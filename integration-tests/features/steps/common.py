"""Common steps for macrocontainer redeployment testing

All steps in this file should only assume access to the LeApp CLI client,
to allow testing of behaviour without the DBus service running.
"""
from behave import given, when, then, step
from hamcrest import assert_that, equal_to, not_none, greater_than

##############################
# Local VM management
##############################

@given("the local virtual machines")
def create_local_machines(context):
    """Accepts a table of local virtual machine definitions, consisting of:

    * name: the name to be used to refer to the VM in later test steps
    * definition: the definition directory to use in integration-tests/vmdefs
    * ensure_fresh: set to 'yes' to destroy an existing VM instead of reusing it

    Note: Ansible VM provisioning playbooks are always executed by this step,
    even when *ensure_fresh* is set to 'no'. For faster test execution, relying
    on Ansible to restore the VM to a known state is recommended, rather than
    requiring a full VM create/destroy cycle.
    """
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

@when("{source_vm} is redeployed to {target_vm} as a macrocontainer with ports {ports} forwarded")
def redeploy_vm_as_macrocontainer_with_ports(context, source_vm, target_vm, ports):
    """Uses leapp-tool.py to redeploy the given source VM

    Both *source_vm* and *target_vm* must be named in a previous local
    virtual machine creation table.
    """
    context.redeployment_source = source_vm
    context.redeployment_target = target_vm
    ports = ports.split(',')
    args = ['{}={}'.format(*spec) 
            for spec in zip(['--tcp-port'] * len(ports), 
                            ['{}:{}'.format(p, p) for p in ports])]
    result = context.cli_helper.redeploy_as_macrocontainer(source_vm, target_vm, list(args))
    assert_that(result.local_vm_count, greater_than(1), "At least 2 local VMs")
    assert_that(result.source_ip, not_none(), "Valid source IP")
    assert_that(result.target_ip, not_none(), "Valid target IP")
    context.redeployment_source_ip = result.source_ip
    context.redeployment_target_ip = result.target_ip


@when("{source_vm} is redeployed to {target_vm} as a macrocontainer")
def redeploy_vm_as_macrocontainer(context, source_vm, target_vm):
    """Uses leapp-tool.py to redeploy the given source VM

    Both *source_vm* and *target_vm* must be named in a previous local
    virtual machine creation table.
    """
    context.redeployment_source = source_vm
    context.redeployment_target = target_vm
    result = context.cli_helper.redeploy_as_macrocontainer(source_vm, target_vm)
    assert_that(result.local_vm_count, greater_than(1), "At least 2 local VMs")
    assert_that(result.source_ip, not_none(), "Valid source IP")
    assert_that(result.target_ip, not_none(), "Valid target IP")
    context.redeployment_source_ip = result.source_ip
    context.redeployment_target_ip = result.target_ip


##############################
# Service status checking
##############################

@then("the HTTP {status:d} response on port {tcp_port:d} should match within {time_limit:g} seconds")
def check_http_responses_match(context, tcp_port, status, time_limit):
    """Checks a macrocontainer response matches the original VM's response

    The source and target VM are inferred from the most recent preceding
    redeployment step.
    """
    original_ip = context.redeployment_source_ip
    redeployed_ip = context.redeployment_target_ip
    assert_that(original_ip, not_none(), "Valid original IP")
    assert_that(redeployed_ip, not_none(), "Valid redeployment IP")
    context.http_helper.compare_redeployed_response(
        original_ip,
        redeployed_ip,
        tcp_port=tcp_port,
        status=status,
        wait_for_target=time_limit
    )

@then("the HTTP {status:d} response against {path} on port {tcp_port:d} should match within {time_limit:g} seconds")
def check_http_response_match_by_path(context, tcp_port, path, status, time_limit):
    """Checks a macrocontainer response matches the original VM's response on specified URL

    
    """
    original_ip = context.redeployment_source_ip
    redeployed_ip = context.redeployment_target_ip
    assert_that(original_ip, not_none(), "Valid original IP")
    assert_that(redeployed_ip, not_none(), "Valid redeployment IP")
    context.http_helper.compare_redeployed_response_loop(
        original_ip,
        redeployed_ip,
        tcp_port=tcp_port,
        wait_for_target=time_limit,
        status=status,
        path=path
    )
