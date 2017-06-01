"""Steps to test the demonstration Cockpit plugin"""
from behave import given, when, then
from hamcrest import (
    assert_that, equal_to, greater_than, greater_than_or_equal_to
)

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
def ensure_demo_plugin_is_installed(context):
    """Ensures expected symlinks into the testing repo exist"""
    # Copy the demo plugin to the demo user's home directory
    demo_user = context.demo_user
    demo_user.install_plugin()
    user_plugin_dir = str(demo_user.USER_DIR / ".local/share/cockpit/leapp")
    assert_that(os.path.exists(user_plugin_dir), "User plugin not installed")
    # Check the rest of the repo is linked where the plugin will find it
    leapp_dir_link = pathlib.Path("/opt/leapp")
    desired_leapp_target = context.BASE_REPO_DIR
    _ensure_expected_link(leapp_dir_link, desired_leapp_target)

@when("the demonstration user visits the {menu_item} page")
def visit_demo_page(context, menu_item):
    """Clicks on the named menu item in the top level Cockpit menu"""
    context.demo_session = session = DemoCockpitSession(context)
    session.login()
    session.open_plugin(menu_item)

@then("the local VMs should be listed within {time_limit:g} seconds")
def check_demo_machine_listing(context, time_limit):
    """Checks contents and response time for the demo plugin"""
    session = context.demo_session
    expected_machines = context.vm_helper.machines
    expected_hosts = sorted(host for name, host in expected_machines.items())
    missing = session.list_missing_machines(expected_hosts, time_limit)
    assert_that(missing, equal_to([]), "Machines missing from listing")

@when("the demonstration user redeploys {source_vm} to {target_vm}")
def redeploy_vm_via_plugin(context, source_vm, target_vm):
    session = context.demo_session
    gethost = context.vm_helper.get_hostname
    session.start_vm_redeployment(gethost(source_vm), gethost(target_vm))
    session.wait_for_redeployment_to_start(10)

@then("the redeployment should be reported as complete within {time_limit:g} seconds")
def check_demo_redeployment_result(context, time_limit):
    session = context.demo_session
    session.wait_for_successful_redeployment(time_limit)


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

def _token_hex(nbytes=32):
    return binascii.hexlify(os.urandom(nbytes)).decode('ascii')

import tempfile
from crypt import crypt
import shutil
import pathlib

class DemoCockpitUser(object):
    """Cockpit user that's set up to run the demo"""

    def __init__(self, context):
        self._app_plugin_source_dir = str(context.BASE_REPO_DIR / "cockpit")
        self.username = username = "leapp-" + _token_hex(8)
        self.password = _token_hex()
        temp = pathlib.Path(tempfile.gettempdir())
        self.BASE_DIR = base_dir = temp / _token_hex(8)
        self.USER_DIR = base_dir / username
        context.scenario_cleanup.callback(self.destroy)

    def create(self):
        """Create a local user with required permissions to run the demo"""
        base_dir = self.BASE_DIR
        base_dir.mkdir(exist_ok=True)
        _run_command("sudo", "useradd",
                     "--groups", "libvirt,wheel",
                     "--password", crypt(self.password),
                     "-M", "--base-dir", str(base_dir),
                     self.username)
        # Sanity check and adds info to test logs
        print(_run_command("id", self.username))
        # We create the home directory manually, as asking useradd to do it
        # triggers an SELinux error (presumably due to the use of tmpfs)
        self.USER_DIR.mkdir()
        self._fix_dir_permissions()

    def _fix_dir_permissions(self, dir_to_fix=None):
        # Ensure all the user's files are owned by the demo user,
        # but can still be accessed via the gid running the test suite
        if dir_to_fix is None:
            dir_to_fix = str(self.USER_DIR)
        _run_command("chmod", "-R", "770", dir_to_fix)
        _run_command("sudo", "chown", "-R", self.username, dir_to_fix)

    def install_plugin(self):
        """Install the Cockpit plugin into the demo user's home directory"""
        cockpit_plugin_dir = self.USER_DIR / ".local" / "share" / "cockpit"
        cockpit_plugin_dir.mkdir(parents=True)
        user_plugin_dir = str(cockpit_plugin_dir / "leapp")
        # We make a full copy of the plugin source, so its covered by
        # the permissions changes below and Cockpit will load it
        shutil.copytree(self._app_plugin_source_dir, user_plugin_dir)
        self._fix_dir_permissions(str(cockpit_plugin_dir))

    def destroy(self):
        """Destroy the created test user"""
        # Allow some time for the browser session to fully close down
        deadline = 1 + time.monotonic()
        while time.monotonic() < deadline:
            time.sleep(0.1)
            try:
                _run_command("sudo", "userdel", "-r", self.username)
            except subprocess.CalledProcessError as exc:
                if b"currently used" in exc.stderr:
                    print("User still in use, waiting 100 ms to try again")
                    continue
            break
        shutil.rmtree(str(self.BASE_DIR))

def _ensure_expected_link(symlink, expected_target):
    """Ensure a symlink resolves to the expected target"""
    assert_that(symlink.resolve(), equal_to(expected_target))

import time
import splinter

# Map from plugin menu entries to expected iframe names
KNOWN_PLUGINS = {
   "Le-App": "cockpit1:localhost/leapp/leapp"
}

class DemoCockpitSession(object):
    """Splinter browser session to work with the Cockpit plugin"""
    def __init__(self, context):
        self._user = context.demo_user
        self._browser = browser = splinter.Browser()
        self._cockpit_url = "http://localhost:9090"
        self._plugin_frame = None
        self._scenario_cleanup = cleanup = context.scenario_cleanup
        cleanup.enter_context(browser)

    def login(self):
        """Logs into Cockpit using the test user's credentials

        Ensures password based privilege escalation is enabled when logging in
        """
        browser = self._browser
        user = self._user
        browser.visit(self._cockpit_url)
        assert_that(browser.status_code.is_success(), "Failed to load login page")
        # browser.fill_form looks form elements up by name rather than id, so we
        # find and populate the form elements individually
        browser.find_by_id("login-user-input").fill(user.username)
        browser.find_by_id("login-password-input").fill(user.password)
        browser.find_by_id("authorized-input").check()
        browser.find_by_id("login-button").click()
        self._scenario_cleanup.callback(self.logout)
        self._logged_in = True

    def logout(self):
        """Logs out of Cockpit, allowing the test user to be deleted"""
        self._plugin_frame = None
        self._browser.find_by_id("navbar-dropdown").click()
        self._browser.find_by_id("go-logout").click()

    def open_plugin(self, menu_item):
        """Opens the named plugin tab from the Cockpit navigation menu"""
        if not self._logged_in:
            raise RuntimeError("Must log in before accessing app plugin")
        if menu_item not in KNOWN_PLUGINS:
            raise RuntimeError("Unknown Cockpit plugin: {}".format(menu_item))
        browser = self._browser
        # Allow some time for Cockpit to render after initial login
        found_plugin_name = browser.is_text_present(menu_item, wait_time=2)
        err_msg = "{!r} menu item not found on page".format(menu_item)
        assert_that(found_plugin_name, err_msg)
        browser.click_link_by_partial_text(menu_item)
        frame_name = KNOWN_PLUGINS[menu_item]
        found_app = browser.is_element_present_by_name(frame_name, wait_time=2)
        err_msg = "Plugin iframe {!r} not found on page".format(frame_name)
        assert_that(found_app, err_msg)
        _enter_context = self._scenario_cleanup.enter_context
        self._plugin_frame = _enter_context(browser.get_iframe(frame_name))

    @property
    def plugin_frame(self):
        result = self._plugin_frame
        if result is None:
            raise RuntimeError("Must open app plugin before querying content")
        return result

    def list_missing_machines(self, expected_hostnames, time_limit):
        """Checks the given machine hostnames are visible on the current page

        Returns a list of hostnames that were NOT found on the page
        """
        deadline = time.monotonic() + time_limit
        missing = set(expected_hostnames)
        # Query the page state every 100 ms until either all expected
        # machines are listed or the deadline expires
        option_found = self.plugin_frame.find_by_value
        while missing and time.monotonic() < deadline:
            time.sleep(0.1)
            for hostname in list(missing):
                if option_found(hostname):
                    missing.remove(hostname)
        return sorted(missing)

    def start_vm_redeployment(self, source_hostname, target_hostname):
        """Selects source & target machine, then starts a migration"""
        frame = self.plugin_frame
        frame.choose("target-machine", target_hostname)
        frame.choose("source-machine", source_hostname)
        assert_that(frame.is_text_present("discovered ports", wait_time=20))
        migrate = frame.find_by_id("migrate-button").first
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            time.sleep(0.1)
            # TODO: Switch to a supported public API for this check
            #  RFE: https://github.com/cobrateam/splinter/issues/544
            if migrate._element.is_enabled():
                break
        else:
            assert_that(False, "Selecting source & target failed to allow migration")
        migrate.click()

    def wait_for_redeployment_to_start(self, time_limit):
        frame = self.plugin_frame
        assert_that(frame.is_text_present("Migrating ", wait_time=time_limit),
                    "Failed to start migration")
        time.sleep(0.1) # Immediate check for argument parsing failure
        assert_that(frame.is_text_not_present("Command failed"),
                    "Migration operation immediately reported failure")

    def wait_for_successful_redeployment(self, time_limit):
        frame = self.plugin_frame
        assert_that(frame.is_text_present("> done", wait_time=time_limit),
                    "Migration failed to complete within time limit")
        assert_that(frame.is_text_not_present("Command failed"),
                    "Migration operation reported failure")
        assert_that(frame.is_text_present("Command completed successfully"),
                    "Migration operation did not report success")
