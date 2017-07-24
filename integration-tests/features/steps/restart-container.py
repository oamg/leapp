"""Steps to test docker restart feature"""
from behave import then
from behave import when
from hamcrest import assert_that, equal_to


@then("container named {container_name} should be restarted and running")
def get_container_status(context, container_name):
    cmd = ["sudo", "docker", "inspect", "-f", "{{.State.Running}}", container_name]
    result = context.vm_helper.run_remote_command(context.migration_target, *cmd, ignore_errors=True)
    assert_that(result.strip(), equal_to("true"))

@when("docker is restarted")
def restart_docker(context):
    cmd = ["sudo", "systemctl", "restart", "docker"]
    context.vm_helper.run_remote_command(context.migration_target, *cmd, ignore_errors=True)
