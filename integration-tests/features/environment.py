import contextlib
import subprocess

# behave adds the features directory to sys.path, so import the testing helpers
from leapp_testing import (
    REPO_DIR, TEST_DIR, install_client,
    VirtualMachineHelper, ClientHelper, RequestsHelper
)

##############################
# Test execution hooks
##############################

# The @skip support here is based on:
# http://stackoverflow.com/questions/36482419/how-do-i-skip-a-test-in-the-behave-python-bdd-framework/42721605#42721605
_AUTOSKIP_TAG = "skip"
_WIP_TAG = "wip"
def _skip_test_group(context, test_group):
    """Decides whether or not to skip a test feature or test scenario

    Test groups are skipped if they're tagged with `@skip` and the `skip` tag
    is not explicitly requested through the command line options.

    The `--wip` option currently overrides `--tags`, so groups tagged with both
    `@skip` *and* `@wip` are also executed when the `wip` tag is requested.
    """
    active_tags = context.config.tags
    autoskip_tag_set = _AUTOSKIP_TAG in test_group.tags
    autoskip_tag_requested = active_tags and active_tags.check([_AUTOSKIP_TAG])
    wip_tag_set = _WIP_TAG in test_group.tags
    wip_tag_requested = active_tags and active_tags.check([_AUTOSKIP_TAG, _WIP_TAG])
    override_autoskip = autoskip_tag_requested or (wip_tag_set and wip_tag_requested)
    skip_group = autoskip_tag_set and not override_autoskip
    if skip_group:
        test_group.skip("Marked with @skip")
    return skip_group

def before_all(context):
    # Basic info about the test repository
    context.BASE_REPO_DIR = REPO_DIR
    context.BASE_TEST_DIR = TEST_DIR

    # Some steps require sudo, so for convenience in interactive use,
    # we ensure we prompt for elevated permissions immediately,
    # rather than potentially halting midway through a test
    subprocess.check_output(["sudo", "echo", "Elevated permissions needed"])

    # Install the CLI for use in the tests
    install_client()

    # Use contextlib.ExitStack to manage global resources
    context._global_cleanup = contextlib.ExitStack()

def before_feature(context, feature):
    if _skip_test_group(context, feature):
        return

    # Use contextlib.ExitStack to manage per-feature resources
    context._feature_cleanup = contextlib.ExitStack()

def before_scenario(context, scenario):
    if _skip_test_group(context, scenario):
        return

    # Each scenario has a contextlib.ExitStack instance for resource cleanup
    context.scenario_cleanup = contextlib.ExitStack()

    # Each scenario gets a VirtualMachineHelper instance
    # VMs are relatively slow to start/stop, so by default, we defer halting
    # or destroying them to the end of the overall test run
    # Feature steps can still opt in to eagerly cleaning up a scenario's VMs
    # by doing `context.scenario_cleanup.callback(context.vm_helper.close)`
    context.vm_helper = vm_helper = VirtualMachineHelper()
    context._global_cleanup.callback(vm_helper.close)

    # Each scenario gets a ClientHelper instance
    context.cli_helper = cli_helper = ClientHelper(context.vm_helper)

    # Each scenario gets a RequestsHelper instance
    context.http_helper = RequestsHelper()

def after_scenario(context, scenario):
    if scenario.status == "skipped":
        return
    context.scenario_cleanup.close()

def after_feature(context, feature):
    if feature.status == "skipped":
        return
    context._feature_cleanup.close()

def after_all(context):
    context._global_cleanup.close()
