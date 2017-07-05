"""Steps to test the "destroy-containers" subcommand"""
from behave import given, then
from hamcrest import assert_that, equal_to
from functools import partial
from json import loads

class ClaimHelper(object):
    """Helper to claim names on a target VM in ways check-target will detect"""
    def __init__(self, run_remote):
        self._run_remote = run_remote

    def make_macrocontainer_dir(self, claimed_name):
        """Create a macrocontainer storage directory with the given name"""
        storage_dir = "/var/lib/leapp/macrocontainers/"
        cmd = ["mkdir", "-p", storage_dir + claimed_name]
        return self._run_remote(*cmd)

    def make_idle_container(self, claimed_name):
        """Create an idle container with the given name"""
        cmd = ["sudo", "docker", "run", "--name", claimed_name, "centos:7"]
        # The tests don't currently clean up arbitrary containers when
        # reprovisioning the target (to allow for containerised system
        # services), so this ignores errors on the assumption they're just
        # "this container already exists"
        return self._run_remote(*cmd, ignore_errors=True)

    def make_idle_macrocontainer(self, claimed_name):
        """Create an idle container with the given name"""
        self.make_macrocontainer_dir(claimed_name)
        return self.make_idle_container(claimed_name)

    def claim_name(self, claimed_name, kind):
        """Claim a name on the target using the nominated kind"""
        claim_method = getattr(self, "make_" + "_".join(kind.split()))
        return claim_method(claimed_name)


@given("the following names claimed on {target}")
def claim_names_on_target_vm(context, target):
    """Accepts a table of claimed names on the target VM, consisting of:

    * name: the name expected to be reported for the claim by check-target
    * kind: the kind of "claim" to create on the target VM

    The following kinds of claims can be specified:

    * "macrocontainer dir": creates an empty macrocontainer storage directory
    * "idle container": creates an idle CentOS 7 container
    * "idle macrocontainer": creates both a container and a storage directory
    """
    run_remote = partial(context.vm_helper.run_remote_command, target)
    helper = ClaimHelper(run_remote)
    claimed_names = set()
    for row in context.table:
        claimed_name = row["name"]
        if claimed_name in claimed_names:
            msg = "Attempted to claim the same name twice: " + claimed_name
            raise RuntimeError(msg)
        helper.claim_name(claimed_name, row["kind"])
        claimed_names.add(claimed_name)
    context._claimed_names = sorted(claimed_names)

@then("checking {target} usability should take less than {time_limit:g} seconds")
def run_check_target(context, target, time_limit):
    """Retrieve claimed names from designated target"""
    context._check_result = {'containers': context.cli_helper.check_target(target, time_limit)}

@then("checking {target} services status should take less than {time_limit:g} seconds")
def run_check_target_status(context, target, time_limit):
    """Retrieve services status from designated target"""
    status = context.cli_helper.check_target_status(target, time_limit)
    print(status)
    context._target_status = loads(status[0])

@then("all claimed names should be reported exactly once")
def check_claimed_names(context):
    """Check claimed names match those in the expected list"""
    assert_that(context._check_result['containers'], equal_to(context._claimed_names))

@then("{service} should be reported as \"{result}\"")
def check_reported_status(context, service, result):
    """Check reported status match those expected"""
    assert_that(context._target_status[service], equal_to(result))
