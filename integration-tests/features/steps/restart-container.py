"""Steps to test docker restart feature"""
from behave import then
from behave import when


@then("container named {container_name} should be restarted and running")
def get_container_status():
    pass


@when("docker is restarted")
def restart_docker():
    pass
