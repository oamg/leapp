"""Steps to test the demonstration Cockpit plugin"""
from behave import given, when, then
from hamcrest import (
    assert_that, equal_to, greater_than, greater_than_or_equal_to
)

import shutil
import pathlib

@given("Cockpit is installed on the testing host")
def check_cockpit_is_installed(context):
    """Checks for the `cockpit-bridge` command"""
    if shutil.which("cockpit-bridge") is None:
        context.scenario.skip("Unable to locate `cockpit-bridge` command")

@given("the demonstration user exists")
def create_demonstration_user(context):
    """Creates a demonstration user for the scenario"""
    context.demo_user = demo_user = DemoCockpitUser(context)
    demo_user.create()

@given("the demonstration plugin is installed")
def ensure_demo_plugin_is_properly_linked(context):
    """Ensures expected symlinks into the testing repo exist"""
    # Link the demo plugin where Cockpit will find it
    demo_plugin_dir = context.demo_user.USER_DIR
    user_plugin_link = demo_plugin_dir / ".local/share/cockpit/leapp"
    desired_plugin_target = context.BASE_REPO_DIR / "cockpit"
    _ensure_expected_link(user_plugin_link, desired_plugin_target)
    # Check the repo is linked where the plugin will find it
    leapp_dir_link = pathlib.Path("/opt/leapp")
    desired_leapp_target = context.BASE_REPO_DIR
    _ensure_expected_link(leapp_dir_link, desired_leapp_target)

@when("the demonstration user visits the {menu_item} page")
def visit_demo_page(context, menu_item):
    """Clicks on the named menu item in the top level Cockpit menu"""
    raise NotImplementedError()

@then("the local VMs should be listed within {time_limit:g} seconds")
def check_demo_machine_listing(context, time_limit):
    """Checks contents and response time for the demo plugin"""
    raise NotImplementedError

# Helper functions and classes
# Note: these are all candidates for moving to the `behave` context
#       where they can use the shared `_run_command` implementation
#       rather than the local variant below

import subprocess

def _run_command(*cmd):
    print("  Running {}".format(cmd))
    output = None
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode()
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        print("=== stdout for failed command ===")
        print(output)
        print("=== stderr for failed command ===")
        print(exc.stderr.decode())
        raise
    return output

import binascii
import os
import tempfile
from crypt import crypt

def _token_hex(nbytes=32):
    return binascii.hexlify(os.urandom(nbytes)).decode('ascii')

class DemoCockpitUser(object):
    """Cockpit user that's set up to run the demo"""
    def __init__(self, context):
        self._app_plugin_dir = context.BASE_REPO_DIR / "cockpit"
        self.username = username = "leapp-" + _token_hex(8)
        self.password = _token_hex()
        self.base_dir = base_dir = tempfile.mkdtemp()
        self.USER_DIR = pathlib.Path(base_dir) / username
        context.scenario_cleanup.callback(self.destroy)

    def create(self):
        # Create local user that's part of the libvirt group
        # and can run sudo without a password
        _run_command("sudo", "useradd",
                     "--groups", "libvirt,wheel",
                     "--password", crypt(self.password),
                     "-M", "--base-dir", self.base_dir,
                     self.username)
        # Sanity check and adds info to test logs
        print(_run_command("id", self.username))
        # We create the home directory manually, as asking useradd to do it
        # triggers an SELinux error (presumably due to the use of tmpfs)
        self.USER_DIR.mkdir()
        # Ensure Cockpit plugin dir exists and has a symlink for the app
        plugin_dir = self.USER_DIR / ".local" / "share" / "cockpit"
        plugin_dir.mkdir(parents=True)
        plugin_link = plugin_dir / "leapp"
        plugin_link.symlink_to(self._app_plugin_dir)
        # Ensure all the user's files are owned by the user,
        # but can still be accessed via the gid running the test suite
        _run_command("chmod", "-R", "770", str(self.USER_DIR))
        _run_command("sudo", "chown", "-R", self.username, str(self.USER_DIR))

    def destroy(self):
        """Destroy the created test user"""
        _run_command("sudo", "userdel", "-r", self.username)
        shutil.rmtree(self.base_dir)


def _ensure_expected_link(symlink, expected_target):
    """Ensure a symlink resolves to the expected target"""
    assert_that(symlink.resolve(), equal_to(expected_target))
