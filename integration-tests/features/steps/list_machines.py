"""Steps to test the "list-machines" subcommand"""
from behave import then
from hamcrest import (
    assert_that, equal_to, greater_than, greater_than_or_equal_to
)

import json

def _check_machine_listing_contents(context, cmd_output, *, shallow):
    """Checks for expected contents in a machine listing"""
    expected_hostnames = set(context.vm_helper.machines.values())
    listing = json.loads(cmd_output)["machines"]
    # Check number of entries
    assert_that(len(listing), greater_than_or_equal_to(len(expected_hostnames)))
    # Check expected hostnames were found
    found_hostnames = set(vm["hostname"] for vm in listing)
    assert_that(found_hostnames, greater_than_or_equal_to(expected_hostnames))
    # Check shallow listing omits package details
    # while full listing includes them
    if shallow:
        for vm in listing:
            assert_that(vm["os"]["packages"], equal_to([]))
    else:
        for vm in listing:
            assert_that(len(vm["os"]["packages"]), greater_than(0))
    # TODO: Check more expected details of the listing output

@then("a shallow machine listing should take less than {time_limit:g} seconds")
def check_shallow_machine_listing(context, time_limit):
    """Checks contents and response time for a shallow machine listing"""
    output = context.cli_helper.check_response_time(
        ["list-machines", "--shallow"],
        time_limit
    )
    _check_machine_listing_contents(context, output, shallow=True)

@then("a full machine listing should take less than {time_limit:g} seconds")
def check_full_machine_listing(context, time_limit):
    """Checks contents and response time for a full machine listing"""
    output = context.cli_helper.check_response_time(
        ["list-machines"],
        time_limit
    )
    _check_machine_listing_contents(context, output, shallow=False)

