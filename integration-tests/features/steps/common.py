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

@when("{source_vm} is redeployed to {target_vm} as a macrocontainer")
def redeploy_vm_as_macrocontainer(context, source_vm, target_vm):
    """Uses leapp-tool.py to redeploy the given source VM

    Both *source_vm* and *target_vm* must be named in a previous local
    virtual machine creation table.
    """
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

@then("the HTTP {status:d} response on port {tcp_port:d} should match within {wait_duration:g} seconds")
def check_http_responses_match(context, tcp_port, status, wait_duration):
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
        wait_for_target=wait_duration
    )
