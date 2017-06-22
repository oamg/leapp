"""Steps to test the "scan-ports" subcommand"""
from behave import then, when
from hamcrest import assert_that, equal_to
from json import loads
from leapp_testing import freezer
import subprocess


def _get_hostname(context, name):
    return context.vm_helper.get_hostname(name)

def _assert_discovered_ports(ports, expected_ports):
    ports = freezer(loads(ports))
    expected_ports = freezer(loads(expected_ports))

    print(expected_ports)
    print(ports)

    assert expected_ports & ports == expected_ports


@then("get list of discovered ports from {vm_source_name} which will be forwarded to {vm_target_name}")
def check_specific_ports_used_by_vm(context, vm_source_name, vm_target_name):
    """check if ports 22,80,111 are open and forwarded to 9022,80,112"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80],[112,111]]"
    _assert_discovered_ports(ports, expected_ports)

@then("get list of discovered ports on {vm_source_name} which will be forwarded to {vm_target_name} and override port {source_port} to {target_port}")
def check_specific_ports_used_by_vm_with_override(context, vm_source_name, vm_target_name, source_port, target_port):
    """check if ports 22,80,111 are open and forwarded to 9022,8080,112"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(target_port, source_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[{},{}],[112,111]]".format(target_port, source_port)
    _assert_discovered_ports(ports, expected_ports)

@then("get list of discovered ports on {vm_source_name} which will be forwarded to {vm_target_name} and add port {source_port} to {target_port} after collision detection")
def check_specific_ports_used_by_vm_with_addition_and_override(context, vm_source_name, vm_target_name, source_port, target_port):
    """check if ports 22,80,111 are open and forwarded to 9022,8080,112"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(target_port, source_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80],[81,8080],[112,111]]"
    _assert_discovered_ports(ports, expected_ports)

@then("get list of discovered ports on {vm_source_name} which will be forwarded to {vm_target_name} and add port {source_port} to {target_port}")
def check_specific_ports_used_by_vm_with_addition(context, vm_source_name, vm_target_name, source_port, target_port):
    """check if ports 22,80,111,8080 are open and forwarded to 9022,8080,112,8080"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(source_port, target_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80],[112,111],[{},{}]]".format(target_port, source_port)
    _assert_discovered_ports(ports, expected_ports)

@then("get list of user defined ports from {vm_source_name} which will be forwarded to {vm_target_name} - port {target_port_0}, port {target_port_1}")
def check_user_defined_ports(context, vm_source_name, vm_target_name, target_port_0, target_port_1):
    """check if ports 22,80,111,8080 are open and forwarded to 9022,8080,111,8080"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "--ignore-default-port-map", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(target_port_0, target_port_0), "{}:{}".format(target_port_1, target_port_1)],
        time_limit=60
    )

    expected_ports = "[[{},{}],[{},{}]]".format(target_port_0, target_port_0, target_port_1, target_port_1)
    _assert_discovered_ports(ports, expected_ports)


@then('get list of discovered ports on {vm_source_name} which will be forwarded to {vm_target_name} and disable port {excluded_port}')
def check_specific_ports_used_by_vm_and_remove_some(context, vm_source_name, vm_target_name, excluded_port):
    """check if ports 22,80,111,8080 are open and forwarded to 9022,8080,112,8080"""

    ports = context.cli_helper.check_response_time(
            ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--no-tcp-port", "{}".format(excluded_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80]]"
    _assert_discovered_ports(ports, expected_ports)

@then('get list of discovered ports on {vm_source_name} which will be forwarded to {vm_target_name} and port {add_port} will not be added')
def check_specific_ports_used_by_vm_add_and_remove(context, vm_source_name, vm_target_name, add_port):
    """check if ports 22,80,111,1111 are open and forwarded to 9022,8080,112"""

    ports = context.cli_helper.check_response_time(
        ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--no-tcp-port", "{}".format(add_port), "--tcp-port", "{}:{}".format(add_port, add_port)],
        time_limit=60
    )
    expected_ports = "[[9022,22],[80,80],[112,111]]"
    _assert_discovered_ports(ports, expected_ports)


@when('A manually mapped {vm_source_name} port {source_port} is already used on {vm_target_name} port {target_port}')
def collision_detect_source_target(context, vm_source_name, vm_target_name, source_port, target_port):
    return_code = 0
    try:
        context.cli_helper.check_response_time(
            ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:{}".format(source_port, target_port)],
            time_limit=60
        )
    except subprocess.CalledProcessError as e:
        return_code = e.returncode

    context.return_code = return_code

@when("A manually mapped {vm_target_name} port {target_port} is used multiple times for different {vm_source_name} port")
def collision_detect_target_target(context, vm_source_name, vm_target_name, target_port):
    return_code = 0
    try:
        context.cli_helper.check_response_time(
            ["migrate-machine", "-p", "-t", _get_hostname(context, vm_target_name), _get_hostname(context, vm_source_name), "--tcp-port", "{}:111".format(target_port), "{}:112".format(target_port)],
            time_limit=60
        )
    except subprocess.CalledProcessError as e:
        return_code = e.returncode

    context.return_code = return_code

@then("An exception will be raised and tool will exit")
def colision_detect_result(context):
   assert_that(context.return_code, not equal_to(0))

