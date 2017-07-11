"""Steps to test the "destroy-containers" subcommand"""
from behave import then
from hamcrest import assert_that, equal_to, not_, is_in


@then("destroying {container} on {target} should take less than {time_limit:g} seconds")
def check_destroy_container(context, container, target, time_limit):
    """Destroy named container on named VM"""
    claimed_names = getattr(context, "_claimed_names")
    if not claimed_names:
        raise RuntimeError("Claim names in test scenario setup to use this step")
    context.cli_helper.check_response_time(
        ["destroy-container", "-t", context.vm_helper.get_ip_address(target), container],
        time_limit,
        use_default_identity=True
    )
    if container in claimed_names:
        claimed_names.remove(container)
    context._reported_names = context.cli_helper.check_target(target)

@then('"{container}" should no longer be reported as in use')
def check_deleted_name_no_longer_reported(context, container):
    """Check deleted container is no longer reported as in use"""
    assert_that(container, not_(is_in(context._reported_names)))

@then("all remaining claimed names should still be reported as in use")
def check_other_claimed_names(context):
    """Check claimed names match those in the expected list"""
    assert_that(context._reported_names, equal_to(context._claimed_names))
