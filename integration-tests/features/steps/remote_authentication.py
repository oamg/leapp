"""Steps for end-to-end testing of remote authentication configuration"""
from behave import given, then

import os

@given("the tests are being run as root")
def skip_unless_running_as_root(context):
    """Skips the scenario if the tests are run as a non-root user"""
    if os.getuid() != 0:
        context.scenario.skip("This scenario can only be run as root")

def _make_auth_test_command(context, target):
    """Create a leapp-tool command to test remote authentication"""
    return ["check-target", "-t", context.vm_helper.get_hostname(target)]

@given("the default identity file is not registered with ssh-agent")
def ensure_ssh_agent_is_running(context):
    context.cli_helper.remove_default_ssh_key()

@then("{target} should be accessible using the default identity file")
def check_remote_access_with_identity_file(context, target):
    """Check remote machine access using the default identity file"""
    context.cli_helper.check_response_time(
        _make_auth_test_command(context, target),
        time_limit=20
    )

@then("{target} should be accessible using the default password")
def check_remote_access_with_interactive_password_entry(context, target):
    """Check remote machine access using the default user & password"""
    context.cli_helper.check_response_time(
        _make_auth_test_command(context, target),
        time_limit=20
    )


@then("{target} should be accessible using ssh-agent")
def check_remote_access_with_ssh_agent(context, target):
    """Check remote machine access using ssh-agent (the default)"""
    context.cli_helper.check_response_time(
        _make_auth_test_command(context, target),
        time_limit=20,
        specify_default_user=True
    )
