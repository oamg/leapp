"""Steps to test the "scan-ports" subcommand"""
from behave import then
from hamcrest import assert_that
from hamcrest import equal_to 
from json import loads

def _sort_ports(ports):
    return sorted(ports, key = lambda x: x[0])

def _get_hostname(context, name):
    return context.vm_helper.get_hostname(name) 

def _assert_discovered_ports(ports, expected_ports):
    ports = _sort_ports(loads(ports))
    expected_ports = _sort_ports(loads(expected_ports))

    print(expected_ports)
    print(ports)

    assert_that(ports, equal_to(expected_ports))


@then("get list of discovered ports from {vm_source_name} which will be forwared from {vm_target_name}")
def check_specific_ports_used_by_vm(context, vm_source_name, vm_target_name):
    """check if ports 22,80,111 are open and forwarded to 9022,80,111"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80],[111,111]]"
    _assert_discovered_ports(ports, expected_ports)
     
@then("get list of discovered ports on {vm_source_name} which will be forwarded from {vm_target_name} and override port {source_port} to {target_port}")
def check_specific_ports_used_by_vm_with_override(context, vm_source_name, vm_target_name, source_port, target_port):
    """check if ports 22,80,111 are open and forwarded to 9022,8080,111"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(source_port, target_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[{},{}],[111,111]]".format(target_port, source_port)
    _assert_discovered_ports(ports, expected_ports)

@then("get list of discovered ports on {vm_source_name} which will be forwarded from {vm_target_name} and add port {source_port} to {target_port}")
def check_specific_ports_used_by_vm_with_addition(context, vm_source_name, vm_target_name, source_port, target_port):
    """check if ports 22,80,111,8080 are open and forwarded to 9022,8080,111,8080"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(source_port, target_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80],[111,111],[{},{}]]".format(target_port, source_port)
    _assert_discovered_ports(ports, expected_ports)

@then("get list of user defined ports from {vm_source_name} which will be forwarded from {vm_target_name} - port {target_port_0}, port {target_port_1}")
def check_user_defined_ports(context, vm_source_name, vm_target_name, target_port_0, target_port_1):
    """check if ports 22,80,111,8080 are open and forwarded to 9022,8080,111,8080"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "--ignore-default-port-map", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(target_port_0, target_port_0), "{}:{}".format(target_port_1, target_port_1)],
        time_limit=60
    )

    expected_ports = "[[{},{}],[{},{}]]".format(target_port_0, target_port_0, target_port_1, target_port_1)
    _assert_discovered_ports(ports, expected_ports)
