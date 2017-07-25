"""Check fsfreeze status"""
from behave import then, when
from hamcrest import assert_that, equal_to
import subprocess

FSFREEZE_TEST_FILE_PATH = "/tmp/test_freeze"
FSFREEZE_BIN_PATH       = "/sbin/fsfreeze"

FSFREEZE_MOCK_SCRIPT    = """#!/bin/sh
touch {}
""".format(FSFREEZE_TEST_FILE_PATH)


def _get_hostname(context, name):
    return context.vm_helper.get_hostname(name)

def _clean_test(context, machine):
    context.vm_helper.run_remote_command(machine, "sudo", "rm", "-f", FSFREEZE_TEST_FILE_PATH)

def _replace_fsfreeze_bin(context, machine):
    _clean_test(context, machine)

    context.vm_helper.run_remote_command(machine, "sudo", "mv", FSFREEZE_BIN_PATH, "{}.back".format(FSFREEZE_BIN_PATH))
    context.vm_helper.run_remote_command(machine, 
        "sudo -i <<< \"echo '{}' > {}\"".format(FSFREEZE_MOCK_SCRIPT, FSFREEZE_BIN_PATH) 
    )
    context.vm_helper.run_remote_command(machine, "sudo", "chmod", "+x", FSFREEZE_BIN_PATH)

def _restore_fsfreeze_bin(context, machine):
    context.vm_helper.run_remote_command(machine, "sudo", "mv", "-f", "{}.back".format(FSFREEZE_BIN_PATH), FSFREEZE_BIN_PATH)
    _clean_test(context, machine)

def _check_if_system_was_locked(context, machine):
    try:
        context.vm_helper.run_remote_command(machine, "ls", FSFREEZE_TEST_FILE_PATH)
        return True
    except subprocess.CalledProcessError:
        return False

@when("{source} is migrated to {target} and fs is {not_frozen} frozen")
@when("{source} is migrated to {target} and fs is frozen")
def test_migrate_fsfreeze(context, source, target, not_frozen=None):
    result = None 
    expect_frozen = (not_frozen is None)

    try:
        cmd = ["migrate-machine", "--force-create", "-t", _get_hostname(context, target), _get_hostname(context, source)]
        if not expect_frozen:
            cmd += ["--freeze-fs", "n"]

        _replace_fsfreeze_bin(context, source)
        migration = context.cli_helper.check_response_time(
            cmd, 
            time_limit=100,
            use_default_identity=True
        )
        result = _check_if_system_was_locked(context, source) 
    finally:
        # restore original command & clean, this may fail if fsfreeze 
        # command wasn't replaced
        try:
            _restore_fsfreeze_bin(context, source)
        except subprocess.CalledProcessError:
            pass

    context.was_frozen = result

@then("source FS will {not_frozen} be frozen")
@then("source FS will be frozen")
def test_frozen_fs(context, not_frozen=None):
    expect_frozen = (not_frozen is None)

    assert_that(expect_frozen, equal_to(context.was_frozen))
