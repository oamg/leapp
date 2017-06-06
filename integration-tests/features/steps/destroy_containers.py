"""Steps to test the "destroy-containers" subcommand"""
from behave import then


@then("destroying existing macrocontainers on {target} should take less than {time_limit:g} seconds")
def check_destroy_containers(context, target, time_limit):
    """check if exisiting containers have been destroyed"""
    context.cli_helper.check_response_time(
        ["destroy-containers", context.vm_helper.get_hostname(target)],
        time_limit,
        use_default_identity=True
    )
