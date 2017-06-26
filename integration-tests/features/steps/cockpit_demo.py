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

@when("enters {source_vm}'s IP address as the import source")
def step_impl(context, source_vm):
    session = context.demo_session
    source_ip = context.vm_helper.get_ip_address(source_vm)
    context.demo_user.register_host_key(source_ip)
    session.enter_source_ip(source_ip)
    session.wait_for_active_import_button(10)

@when('clicks the "Import" button')
def import_app_via_plugin(context):
    session = context.demo_session
    session.start_app_import()
    session.wait_for_app_import_to_start(10)

@then("the app import should be reported as complete within {time_limit:g} seconds")
def check_app_import_result(context, time_limit):
    session = context.demo_session
    session.wait_for_successful_app_import(time_limit)

# Helper functions and classes
# Note: these are all candidates for moving into a `leapp_testing` submodule
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
        self.BASE_REPO_DIR = context.BASE_REPO_DIR
        context.scenario_cleanup.callback(self.destroy)
        self._ssh_dir = self.USER_DIR / '.ssh'
        self._user_key = self._ssh_dir / 'id_rsa'
        self._user_known_hosts = self._ssh_dir / 'known_hosts'

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
        self._ssh_dir.mkdir()
        self._fix_dir_permissions()
        self._setup_ssh_key()

    def _setup_ssh_key(self):
        key_path = str(self.BASE_REPO_DIR / 'integration-tests' / 'config' / 'leappto_testing_key')
        user_key = str(self._user_key)
        # Copy the testing key in as the user's default key
        _run_command("sudo", "cp", key_path, user_key)
        _run_command("sudo", "cp", key_path + ".pub", user_key + ".pub")

        # Make sure the user's SSH directory has the correct permissions
        ssh_dir = str(self._ssh_dir)
        _run_command("sudo", "chown", "-R", self.username, ssh_dir)
        _run_command("sudo", "chmod", "-R", "u=Xrw,g=u,o=", ssh_dir)
        _run_command("sudo", "chmod", "600", user_key)
        _run_command("sudo", "chmod", "644", user_key + ".pub")
        # Make sure the user's SSH directory has the correct SELinux labels
        _run_command("sudo", "chcon", "-R", "unconfined_u:object_r:ssh_home_t:s0", ssh_dir)

    def _fix_dir_permissions(self, dir_to_fix=None):
        # Ensure all the user's files are owned by the demo user,
        # but can still be accessed via the gid running the test suite
        if dir_to_fix is None:
            dir_to_fix = str(self.USER_DIR)
        _run_command("chmod", "-R", "u=Xrw,g=u,o=", dir_to_fix)
        _run_command("sudo", "chown", "-R", self.username, dir_to_fix)
        # Make sure the user's home directory has the correct SELinux labels
        _run_command("sudo", "chcon", "-R", "unconfined_u:object_r:user_home_t:s0", dir_to_fix)

    def register_host_key(self, source_ip):
        host_key_info = _run_command("ssh-keyscan", "-t", "rsa", source_ip)
        with self._user_known_hosts.open("a") as f:
            f.write(host_key_info)

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
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            time.sleep(0.1)
            try:
                _run_command("sudo", "userdel", "-r", self.username)
            except subprocess.CalledProcessError as exc:
                if b"currently used" in exc.stderr:
                    print("User still in use, waiting 100 ms to try again")
                    continue
            break
        # Ensure the entire temporary tree gets deleted,
        # even the parts now owned by the temporary user
        _run_command("sudo", "rm", "-r", str(self.BASE_DIR))

def _ensure_expected_link(symlink, expected_target):
    """Ensure a symlink resolves to the expected target"""
    assert_that(symlink.resolve(), equal_to(expected_target))

import time
import splinter

# Map from plugin menu entries to expected iframe names
KNOWN_PLUGINS = {
   "Import Apps": "cockpit1:localhost/leapp/leapp"
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

    def enter_source_ip(self, source_ip):
        """Specifies source IP for application to be imported"""
        frame = self.plugin_frame
        source_address = frame.find_by_id("source-address").first
        source_address.fill(source_ip)
        find_apps = frame.find_by_id("scan-source-btn").first
        find_apps.click()

    def wait_for_active_import_button(self, time_limit):
        """Waits for the import button to become active (if it isn't already)"""
        frame = self.plugin_frame
        import_app = frame.find_by_id("import-button")
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            time.sleep(0.1)
            # TODO: Switch to a supported public API for this check
            #  RFE: https://github.com/cobrateam/splinter/issues/544
            if import_app and import_app.first._element.is_enabled():
                break
        else:
            assert_that(False, "Specifying source failed to allow migration")
        self.import_app = import_app

    def start_app_import(self):
        """Selects source & target machine, then starts a migration"""
        self.import_app.click()

    def _dump_failed_command(self):
        """Dump the progress report from a failed web UI command to stdout

        If there is no failed command, dumps all executed commands
        """
        frame = self.plugin_frame
        failure_log = frame.find_by_css("li.failed")
        if not failure_log:
            print("No failed commands reported in UI")
            commands = frame.find_by_css("li.success")
            for command in commands:
                line = command.find_by_css("h4")
                print("UI Command> {}".format(line.text))
        else:
            failure = failure_log.first
            failure.click()
            print("Last executed command failed")
            line = failure.find_by_css("h4")
            print("UI Command> {}".format(line.text))
            progress_lines = frame.find_by_css("span.progress-line")
            for line in progress_lines:
                if line:
                    print("UI Log> {}".format(line.text))
        # Uncomment one of these two lines for live debugging of failures
        # Note: don't check either of these in, as they will hang in CI
        # input("Press enter to resume execution") # Just browser exploration
        # import pdb; pdb.set_trace() # Interactive Python debugging

    def wait_for_app_import_to_start(self, time_limit):
        frame = self.plugin_frame
        started = frame.is_text_present("migrate-machine ", wait_time=time_limit)
        if not started:
            self._dump_failed_command()
        assert_that(started, "Failed to start migration")
        time.sleep(0.1) # Immediate check for argument parsing failure
        already_failed = frame.find_by_css("li.failed")
        if already_failed:
            self._dump_failed_command()

        assert_that(not already_failed,
                    "Migration operation immediately reported failure")

    def wait_for_successful_app_import(self, time_limit):
        frame = self.plugin_frame
        # Wait for the app import operation to complete
        deadline = time.monotonic() + time_limit
        running = frame.find_by_css("li.running")
        while running and time.monotonic() < deadline:
            time.sleep(0.1)
            already_failed = frame.find_by_css("li.failed")
            if already_failed:
                self._dump_failed_command()
                assert_that(not already_failed, "Migration operation failed")
            running = frame.find_by_css("li.running")
        # Confirm that the import operation succeeded
        last_command = frame.find_by_css("li.success")[-1]
        last_command.click()
        success_message = "Imported service is now starting"
        succeeded = frame.is_text_present(success_message)
        if not succeeded:
            self._dump_failed_command()
        assert_that(succeeded, "Migration failed to complete within time limit")
