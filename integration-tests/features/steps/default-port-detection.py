"""Steps to test the "scan-ports" subcommand"""
from behave import then
from hamcrest import assert_that
from json import loads


def _assert_discovered_ports(ports):
    ports = loads(ports)
    assert_that(ports['status'], "success")
    assert_that(ports['ports'].get('tcp', False))
    assert_that(ports['ports']['tcp'].keys(), [22, 80])


#@then("getting information about ports {port_range} used by {vm_ip} should take less than {time_limit:g} seconds")
#def check_specific_ports_used_by_vm(context, vm_ip, port_range, time_limit):
#    """check if ports 22,80 are open"""
#    ports = context.cli_helper.check_response_time(
#        ["port-inspect", "--range", port_range, vm_ip],
#        time_limit
#    )
#    _assert_discovered_ports(ports)
#
#
#@then("getting informations about all used ports by {vm_ip} should take less than {time_limit:g} seconds")
#def check_all_used_ports_by_vm(context, vm_ip, time_limit):
#    """check all used ports by vm, scan should be really fast"""
#    ports = context.cli_helper.check_response_time(
#            ["port-inspect", "--shallow", vm_ip],
#            time_limit,
#            as_sudo=True
#    )
#    _assert_discovered_ports(ports)
