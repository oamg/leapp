"""Common steps for macrocontainer migration testing

All steps in this file should only assume access to the LeApp CLI client,
to allow testing of behaviour without the DBus service running.
"""
from behave import given, when, then
from hamcrest import assert_that, equal_to, is_not, not_none

import shutil

##############################
# Local VM management
##############################


@given("the local virtual machines as {user}")
@given("the local virtual machines")
def create_local_machines(context, user=None):
    """Accepts a table of local virtual machine definitions, consisting of:

    * name: the name to be used to refer to the VM in later test steps
    * definition: the definition directory to use in integration-tests/vmdefs
    * ensure_fresh: set to 'yes' to destroy an existing VM instead of reusing it

    Note: Ansible VM provisioning playbooks are always executed by this step,
    even when *ensure_fresh* is set to 'no'. For faster test execution, relying
    on Ansible to restore the VM to a known state is strongly recommended,
    rather than requiring a full VM create/destroy cycle.

    When the tests are run as a non-root user, specifying 'as root' implies
    'ensure_fresh=yes', even if it is otherwise set to 'no'.
    """
    if user not in (None, "root"):
        msg = "VMs must be started as either root or the current user"
        raise RuntimeError(msg)
    as_root = (user == "root")
    vm_helper = context.vm_helper
    for row in context.table:
        ensure_fresh = (row["ensure_fresh"].lower() == "yes")
        vm_helper.ensure_local_vm(
            row["name"],
            row["definition"],
            destroy=ensure_fresh,
            as_root=as_root,
        )


##############################
# Local container management
##############################

@given("Docker is installed on the testing host")
def check_docker_is_installed(context):
    """Checks for the `docker` command"""
    if shutil.which("docker") is None:
        context.scenario.skip("Unable to locate `docker` command")


##############################
# Leapp commands
##############################

@when("{source_vm} is migrated to {target_vm} as a macrocontainer")
@when("{source_vm} is migrated to {target_vm} as a macrocontainer and {migration_opt} is used for fs migration")
@when("{source_vm} is migrated to {target_vm} as a macrocontainer named {container_name}")
def migrate_vm_as_macrocontainer(context, source_vm, target_vm, migration_opt=None, container_name=None):
    """Uses leapp-tool.py to migrate the given source VM

    Both *source_vm* and *target_vm* must be named in a previous local
    virtual machine creation table.
    """
    context.migration_source = source_vm
    context.migration_target = target_vm
    context.migration_migration_opt = migration_opt
    migrate_app = context.cli_helper.migrate_as_macrocontainer
    output = migrate_app(source_vm, target_vm, migration_opt, container_name=container_name)  # nopep8
    # TODO: Assert specifics regarding expected output


@when("{source_vm} is imported as a macrocontainer")
def import_vm_as_macrocontainer(context, source_vm):
    """Uses leapp-tool.py to migrate the given source VM to the local system

    *source_vm* must be named in a previous local virtual machine creation table.
    """
    # For simplicity, always uses rsync and forced creation
    # (the latter makes it easier to run the tests multiple times locally)
    context.migration_source = source_vm
    context.migration_target = target_vm = "localhost"
    context.migration_migration_opt = migration_opt = "rsync"
    migrate_app = context.cli_helper.migrate_as_macrocontainer  # nopep8
    output = migrate_app(source_vm, target_vm, migration_opt, force_create=True)  # nopep8
    # TODO: Assert specifics regarding expected output


@then("attempting another migration should fail within {time_limit:g} seconds")
def repeat_previous_migration(context, time_limit):
    """Attempts to repeat a previously executed migration command"""
    source_vm = context.migration_source
    target_vm = context.migration_target
    migration_opt = context.migration_migration_opt
    helper = context.cli_helper
    cmd_args = helper.make_migration_command(source_vm, target_vm, migration_opt)
    output = helper.check_response_time(cmd_args, time_limit,
                                        expect_failure=True)
    assert_that(output, is_not(equal_to("")))
    # TODO: Assert specifics regarding expected output


@then('migrating {source_vm} to {target_vm} as "{app_name}" should fail within {time_limit:g} seconds')
def expect_failed_migration(context, source_vm, target_vm, app_name, time_limit):
    context.migration_source = source_vm
    context.migration_target = target_vm
    context.migrated_app = app_name
    context.migration_migration_opt = migration_opt = "rsync"
    helper = context.cli_helper
    cmd_args = helper.make_migration_command(source_vm, target_vm, migration_opt,
                                             container_name=app_name)
    output = helper.check_response_time(cmd_args, time_limit,
                                        expect_failure=True)
    assert_that(output, is_not(equal_to("")))
    # TODO: Assert specifics regarding expected output


@then("attempting another migration with forced creation should succeed within {time_limit:g} seconds")
def force_app_migration(context, time_limit):
    source_vm = context.migration_source
    target_vm = context.migration_target
    app_name = context.migrated_app
    migration_opt = context.migration_migration_opt
    helper = context.cli_helper
    cmd_args = helper.make_migration_command(source_vm, target_vm, migration_opt,
                                             container_name=app_name,
                                             force_create=True)
    output = helper.check_response_time(cmd_args, time_limit)  # nopep8
    # TODO: Assert specifics regarding expected output


##############################
# Service status checking
##############################

@then("the HTTP {status:d} response on port {tcp_port:d} should match within {time_limit:g} seconds")
def check_http_responses_match(context, tcp_port, status, time_limit):
    """Checks a macrocontainer response matches the original VM's response

    The source and target VM are inferred from the most recent preceding
    migration step.
    """
    source_vm = context.migration_source
    target_vm = context.migration_target

    original_ip = context.vm_helper.get_ip_address(source_vm)
    migrated_ip = context.vm_helper.get_ip_address(target_vm)
    assert_that(original_ip, not_none(), "Valid original IP")
    assert_that(migrated_ip, not_none(), "Valid migration IP")
    context.http_helper.compare_migrated_response(
        original_ip,
        migrated_ip,
        tcp_port=tcp_port,
        status=status,
        wait_for_target=time_limit
    )
