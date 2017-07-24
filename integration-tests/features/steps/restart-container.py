"""Steps to test docker restart feature"""
from behave import then
from behave import when


@then("container named {container_name} should be restarted and running")
def get_container_status(context, container_name):
    pass


@when("docker is restarted")
def restart_docker(context):
    pass
