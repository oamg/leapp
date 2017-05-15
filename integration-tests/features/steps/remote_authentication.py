"""Steps for end-to-end testing of remote authentication configuration"""
from behave import given, then

def _make_auth_test_command(context, target):
    """Create a leapp-to command to test remote authentication"""
    # Use destroy-containers, since it's currently the only command
    # that requires remote access, but also only needs a single target VM
    return ["destroy-containers", context.vm_helper.get_hostname(target)]

@given("ssh-agent is running")
def ensure_ssh_agent_is_running(context):
    context.cli_helper.ensure_ssh_agent_is_running(context.scenario_cleanup)

@given("the default identity file is registered with ssh-agent")
def register_default_identity_with_ssh_agent(context):
    context.cli_helper.add_default_ssh_key(context.scenario_cleanup)

@then("{target} should be accessible using the default identity file")
def check_remote_access_with_identity_file(context, target):
    """Check remote machine access using the default identity file"""
    context.cli_helper.check_response_time(
        _make_auth_test_command(context, target),
        time_limit=20,
        complete_identity=True
    )

@then("{target} should be accessible using ssh-agent")
def check_remote_access_with_ssh_agent(context, target):
    """Check remote machine access using ssh-agent (the default)"""
    context.cli_helper.check_response_time(
        _make_auth_test_command(context, target),
        time_limit=20,
        complete_user=True
    )
