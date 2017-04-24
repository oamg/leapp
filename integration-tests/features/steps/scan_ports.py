"""Steps to test the "scan-ports" subcommand"""
from behave import then
from hamcrest import assert_that
from json import loads


@then("getting information about used ports by {vm_ip} from range {port_range}" \
      "should take less than {time_limit:g} seconds")
def check_used_ports_by_vm(context, vm_ip, port_range, time_limit):
    """check if port 80 is open"""
    ports = context.cli_helper.check_response_time(
        ["scan-ports", vm_ip, port_range],
        time_limit
    )
    ports = loads(ports)
    assert_that(ports.get('tcp', False))
    assert_that(ports['tcp'].get('80', False))
