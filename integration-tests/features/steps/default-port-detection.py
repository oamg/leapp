"""Steps to test the "scan-ports" subcommand"""
from behave import then
from hamcrest import assert_that
from json import loads


def _assert_discovered_ports_default_only(ports):
    ports = sort(loads(ports))
    expected_ports = "[[22,9022],[80,80],[111,111]]" 

    assert_that(ports, contains(expected_ports))

@then("getting list of forwarded ports from {vm_source_name} to {vm_target_name}")
def check_specific_ports_used_by_vm(context, vm_source_name, vm_target_name):
    """check if ports 22,80,111 are open and forwarded to 9022,80,111"""

    ports = context.cli_helper.check_response_time(
        ["port-inspect", "-p", "-t", vm_target_name, vm_source_name],
        time_limit=30
    )
    _assert_discovered_ports_default_only(ports)
