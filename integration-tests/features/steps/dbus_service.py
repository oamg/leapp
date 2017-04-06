"""Steps for testing behaviour with the backend DBus service running"""
from behave import given, then
from hamcrest import (
    assert_that, equal_to, greater_than, greater_than_or_equal_to
)

import json

@given("the backend DBus service is running")
def ensure_dbus_service_is_running(context):
    """Ensures the DBus service is currently running"""
    # TODO: Write the service and start it here
    pass

@given("the backend DBus service is not running")
def ensure_dbus_service_is_not_running(context):
    """Ensures the DBus service is not currently running"""
    # TODO: Ensure the backend service isn't running
    pass

@then("the status cache should be populated within {time_limit:g} seconds")
def ensure_dbus_service_cache_is_populated(context, time_limit):
    """Ensures the DBus service's status cache is populated promptly"""
    # TODO: Actually query the service for cache freshness
    pass

