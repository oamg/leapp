Name:       leapp
Version:    0.1
Release:    33
Summary:    leapp tool rpm

Group:      Unspecified
License:    LGPLv2+
URL:        https://github.com/leapp-to/leapp
# git clone https://github.com/leapp-to/leapp
# tito build --tgz --tag=%{version}
Source0:    %{name}-%{version}.tar.gz
BuildArch:  noarch

BuildRequires:   python2-devel
%if 0%{?rhel} && 0%{?rhel} <= 7
BuildRequires:   python-setuptools
BuildRequires:   epel-rpm-macros
%else
BuildRequires:   python2-setuptools
BuildRequires:   python-rpm-macros
%endif

%description
LeApp is a "Minimum Viable Migration" utility that aims to decouple virtualized
applications from the operating system kernel included in their VM image by
migrating them into macro-containers that include all of the traditional
components of a stateful VM (operating system user space, application run-time,
management tools, configuration files, etc), but use the kernel of the
container host rather than providing their own.

%package    tool
Summary:    LeApp is a "Minimum Viable Migration" utility
Requires:   python2-%{name} = %{version}-%{release}

%description tool
LeApp is a "Minimum Viable Migration" utility that aims to decouple virtualized
applications from the operating system kernel included in their VM image by
migrating them into macro-containers that include all of the traditional
components of a stateful VM (operating system user space, application run-time,
management tools, configuration files, etc), but use the kernel of the
container host rather than providing their own.

%package -n python2-%{name}
Summary:    Python libraries of LeApp
Requires:   libguestfs-tools-c
Requires:   libvirt-client
Requires:   libvirt-python
Requires:   nmap
Requires:   sshpass
Requires:   python-enum34
Requires:   rsync
%if 0%{?rhel} && 0%{?rhel} <= 7
Requires:   python-psutil
Requires:   python-nmap
Requires:   python-paramiko
Requires:   python-setuptools
%else
Requires:   python2-nmap
Requires:   python2-paramiko
Requires:   python2-psutil
Requires:   python2-setuptools
%endif

%description -n python2-%{name}
LeApp is a "Minimum Viable Migration" utility that aims to decouple virtualized
applications from the operating system kernel included in their VM image by
migrating them into macro-containers that include all of the traditional
components of a stateful VM (operating system user space, application run-time,
management tools, configuration files, etc), but use the kernel of the
container host rather than providing their own.

%package cockpit
Summary:  Cockpit plugin for LeApp
Requires: cockpit
Requires: docker 
Requires: %{name}-tool = %{version}-%{release}

%description cockpit
LeApp is a "Minimum Viable Migration" utility that aims to decouple virtualized
applications from the operating system kernel included in their VM image by
migrating them into macro-containers that include all of the traditional
components of a stateful VM (operating system user space, application run-time,
management tools, configuration files, etc), but use the kernel of the
container host rather than providing their own.

%prep
%autosetup
sed -i "s/install_requires=/install_requires=[],__fake=/g" src/setup.py

%build
pushd src
%py2_build
popd
# When installed via RPM, always rely on ssh-agent for key management

# update version in Cockpit 
cat <<EOF > cockpit/config.json
{
    "tool-path": "/usr/bin/leapp-tool",
    "tool-workdir": "/usr/bin",
    "version": "%{version}-%{release}"
}
EOF

# update version in CLI 
cat <<EOF > src/leappto/version.py
__version__ = '%{version}-%{release}'
__pkg_name__ = 'leappto'
EOF


cat cockpit/config.json

%install
mkdir -p %{buildroot}%{_datadir}/cockpit/leapp
mkdir -p %{buildroot}%{_sharedstatedir}/leapp/macrocontainers
cp -a cockpit/* %{buildroot}%{_datadir}/cockpit/leapp/

pushd src
%py2_install
popd

%files tool
%doc README.md AUTHORS COPYING
%attr(755, root, root) %{_bindir}/%{name}-tool

%files -n python2-%{name}
%doc README.md AUTHORS COPYING
%{python2_sitelib}/*

%files cockpit
%doc README.md AUTHORS COPYING
%dir %attr (755,root,root) %{_datadir}/cockpit/%{name}
%dir %attr (755,root,root) %{_sharedstatedir}/leapp/macrocontainers
%attr(644, root, root) %{_datadir}/cockpit/%{name}/*


%changelog
* Fri Jun 30 2017 Vinzenz Feenstra <vfeenstr@redhat.com> 0.1-33
- Version bump for 0.1 (vfeenstr@redhat.com)
- Added --freeze-fs option into migrate command, freezefs is not used by
  default (mgazdik@redhat.com)
- Test Leapp RPM in CI (#253) (ncoghlan@gmail.com)
- Removed commented part of code (mgazdik@redhat.com)
- GUI: Port mapping error messaging (mgazdik@redhat.com)
- NOJIRA: update the getstarted with youtube video (vmindru@redhat.com)
- cli: Disable interfering init services on el6 (vfeenstr@redhat.com)
- spec: Fix directory creation (vfeenstr@redhat.com)
- NOJIRA: create /var/lib/leapp/macrocontainers as part of leapp-cockpit
  install (vmindru@redhat.com)
- NOJIRA: udpate getstarted with latest relevant info (vmindru@redhat.com)
- Update Python level CI dependencies (#229) (ncoghlan@gmail.com)
- NOJIRA: peer review (vmindru@redhat.com)
- NOJIRA: right now leapp won't run on a fresh install, it misses docker during
  setup and python  libs (vmindru@redhat.com)
- NOJIRA: right now leapp won't run on a fresh install, it misses docker during
  setup and python  libs (vmindru@redhat.com)
- excluded paths can be empty array now (mgazdik@redhat.com)
- Changed error type and variable name (mgazdik@redhat.com)
- --exclude-path overrides default list (mgazdik@redhat.com)
- CLI: Added support for exclude paths (mgazdik@redhat.com)
- Add excĺuded paths - initial commit (mgazdik@redhat.com)
- NOJIRA: rename repo to leapp (vmindru@redhat.com)
- fix: Use rsync backend by default (podvody@redhat.com)
- stop using _LOCALHOST, simple check if ip is in (127.0.0.1, localhost)
  (mfranczy@redhat.com)
- add 127.0.0.1 to _LOCALHOST const (mfranczy@redhat.com)
- Remove the fix_upstart function, turns out that it was not needed (and
  actually there has been no service named mysqld, only mysql55-mysqld, so the
  mysqld part never did anything). (pcahyna@redhat.com)
- bugfix - do not resolve localhost to ip (mfranczy@redhat.com)
- NOJIRA: update CLI version during RPM build (vmindru@redhat.com)
- NOJIRA: add new tox file with line length (vmindru@redhat.com)
- Clarify purpose of "pipenv install" task (ncoghlan@gmail.com)
- Restore Cockpit plugin test (ncoghlan@gmail.com)
- catch all Exceptions.* (mfranczy@redhat.com)
- resolve fqdn to ip (mfranczy@redhat.com)
- spec: Fix json output (vfeenstr@redhat.com)
- remove unnecessary PortsException - do not raise if hostname is not in
  scan.all_hosts, check only error value (mfranczy@redhat.com)
- integration-tests: Install tito build rpm (vfeenstr@redhat.com)
- integration-tests: Add python2-nmap rpm directly (vfeenstr@redhat.com)
- spec: Fix el7 deps (vfeenstr@redhat.com)
- integration-tests: Install the tito built RPM (vfeenstr@redhat.com)
- spec: Fix psutil dependency (vfeenstr@redhat.com)
- spec: Fix cockpit config generation (vfeenstr@redhat.com)
- Disabled default port mapping for migration executed from UI
  (mgazdik@redhat.com)
- restore previous assertion for port-mapping int-tests (mfranczy@redhat.com)
- instead of using has_items from hamcrest, use more explicit assertion
  (mfranczy@redhat.com)
- fix integration tests (mfranczy@redhat.com)
- check if port-mapping result contains expected ports (mfranczy@redhat.com)
- add missed port - port mapping integration tests (mfranczy@redhat.com)
- psutil package for setup.py (mfranczy@redhat.com)
- psutil package (mfranczy@redhat.com)
- restore PortScanException (mfranczy@redhat.com)
- clean code (mfranczy@redhat.com)
- use psutil.net_connections when it comes to scan localhost
  (mfranczy@redhat.com)
- cli: By default do not check host keys as a workaround (vfeenstr@redhat.com)
- _port_remap is static now, removed default parameters for _port_remap
  (mgazdik@redhat.com)
- ui: Using blue for running commands instead of orange (vfeenstr@redhat.com)
- _port_remap moved into MigrationContext since it is being used by map_ports
  method directly (mgazdik@redhat.com)
- port map can now handle set of target ports per a source port
  (mgazdik@redhat.com)
- ui: Remove debug logging (vfeenstr@redhat.com)
- ui: Add back release and lock for import (vfeenstr@redhat.com)
- ui: Refactor call_leapp to be usable concurrently and add exandable logs
  (vfeenstr@redhat.com)
- Removed checkbox ID port list (mgazdik@redhat.com)
- corrected input port verification (mgazdik@redhat.com)
- Implemented changes suggested in comments (mgazdik@redhat.com)
- Polishing of the code (mgazdik@redhat.com)
- ui: Add custom port mapping form (mgazdik@redhat.com)
- TRELLO-163: adding callback profile to see time details (vmindru@redhat.com)
- TRELLO-163: peer review         add step description         fix date alias
  add time since begining reporting         add timestamps and command  time
  duration execution reporting (vmindru@redhat.com)
- Remove list-machines tests & helpers (ncoghlan@gmail.com)
- Override correct variable name (ncoghlan@gmail.com)
- Configure correct user for host macrocontainer storage (ncoghlan@gmail.com)
- Simplify network interface regex (ncoghlan@gmail.com)
- Update test documentation (ncoghlan@gmail.com)
- Add CLI test case for local machine imports (ncoghlan@gmail.com)
- Fix interface regex on Fedora (ncoghlan@gmail.com)
- Add Docker to CI testing host (ncoghlan@gmail.com)
- ui: Fix visual port collission handling in UI (vfeenstr@redhat.com)
- ui: refactor port adding into separate function for easier reuse
  (vfeenstr@redhat.com)
- ui: Use patternfly compatible classes (vfeenstr@redhat.com)
- ui: Implement port mapping from CLI (vfeenstr@redhat.com)
- cli: Fix target IP list (vfeenstr@redhat.com)
- ui: Add a tooltip to the force create checkbox (vfeenstr@redhat.com)
- ui: Force creation checkbox checked by default (vfeenstr@redhat.com)
- ui: Force create command implementation (vfeenstr@redhat.com)
- Use sys.exit instead of exit (amello@redhat.com)
- Restore handling of missing storage directories (ncoghlan@gmail.com)
- Fix step function name (ncoghlan@gmail.com)
- Add --force-create option to migrate-machine (ncoghlan@gmail.com)
- Add selective destroy-container subcommand (ncoghlan@gmail.com)
- integration-tests: Use ssh-agent in cockpit test (vfeenstr@redhat.com)
- ui: Forward the agent socket (vfeenstr@redhat.com)
- Verify return value of find_machine preventing app to show a bt to user
  (amello@redhat.com)
- enable concurrent runs (kbsingh@karan.org)
- During check-target do not fail if storage dir is missing on target machine
  (amello@redhat.com)
- bugfix: pass container name var into MigrateContext (mfranczy@redhat.com)

* Thu Jun 15 2017 Vinzenz Feenstra <vfeenstr@redhat.com> 0.0.1-32
- ui: Start displaying progress after 'Find apps' was clicked
  (vfeenstr@redhat.com)
- ui: Add target container naming and listing support (vfeenstr@redhat.com)
- ui: Print all command output (vfeenstr@redhat.com)
- Handle running in a Py3 virtual environment (ncoghlan@gmail.com)
- cli: Fix check-target exception for localhost (vfeenstr@redhat.com)
- integration-tests: remove trailing spaces (vfeenstr@redhat.com)
- Remove unused import (amello@redhat.com)
- Removing container dir is unnecessary since containers have different names
  (amello@redhat.com)
- Check target access early in migrate-machine (ncoghlan@gmail.com)
- Update destroy-containers to use check-target (amello@redhat.com)
- Undo ssh calls changes since they were not necessary after merge
  (amello@redhat.com)
- ignore_errors flag for rmtree (mfranczy@redhat.com)
- remove parsed.target condition, now it has default value
  (mfranczy@redhat.com)
- fixed grep for wlp devices (mfranczy@redhat.com)
- localhost as default target (mfranczy@redhat.com)
- cli: Allow to use different user names, identity files etc in migrate-machine
  (vfeenstr@redhat.com)
- Don't enable early target check tests yet (ncoghlan@gmail.com)
- Fix function signature definition (ncoghlan@gmail.com)
- check-target subcommand (ncoghlan@gmail.com)
- Make destroy_containers iterate over all machine containers and delete it
  (amello@redhat.com)
- Make it able to get stdout of a ssh command (amello@redhat.com)
- Make it possible for user to define container name on target machine
  (amello@redhat.com)
- Derive container name from source hostname (amello@redhat.com)
- ui: Change timestamp to ISO8601 format (vfeenstr@redhat.com)
- ui: Fix missing busy_ports variable by referring to the right one
  (vfeenstr@redhat.com)
- UI: command line is shown in progress output (jmikovic@redhat.com)
- Support local docs builds in pipenv config (ncoghlan@gmail.com)
- UI: Fix enter key handler (jsycha@redhat.com)
- UI: IP can be submitted with enter key (jsycha@redhat.com)
- ui: Fix alignment of ports (vfeenstr@redhat.com)
- ui: Skip Cockpit test because we're no longer listing VMs
  (vfeenstr@redhat.com)
- ui: Cleanup of intermediate changes and fixed migrate-machine command
  (vfeenstr@redhat.com)
- ui: Tooltip for port's usage (Used by...) and more cleanup
  (vfeenstr@redhat.com)
- ui: Adding second option for the source style and restyled the logging output
  (vfeenstr@redhat.com)
- ui: Fix source address related text (vfeenstr@redhat.com)
- ui: Default target and source by IP changes (vfeenstr@redhat.com)
- Tidy up port scanning in the test suite (ncoghlan@gmail.com)
- NOJIRA: add waiting message (vmindru@redhat.com)
-    TRELLO-124: amending UI tests    TRELLO-124: renmae le-app in the cockpit
  (vmindru@redhat.com)
- Change output if Source/Target machine is not accessible via SSH
  (amello@redhat.com)
- Add Arthur Mello (artmello) to be able to trigger integration tests
  (amello@redhat.com)
- Clarify use cases for ensure_fresh=yes (ncoghlan@gmail.com)
- Always reprovision even running test VMs (ncoghlan@gmail.com)
- Always run migrate-machine with sudo (ncoghlan@gmail.com)
- Support local docs builds in pipenv config (ncoghlan@gmail.com)
- Add docs regarding VM setup in tests (ncoghlan@gmail.com)
- Don't use ensure_fresh=yes in tests (ncoghlan@gmail.com)
- Use EPEL Ansible package & dependencies (ncoghlan@gmail.com)
- cli: Removed wrong import (vfeenstr@redhat.com)
- integration-tests: Fix the migrate-machine calls (vfeenstr@redhat.com)
- cli: Remove debugging code (vfeenstr@redhat.com)
- cli: More tuning to get the migration to work with localhost and custom
  source (vfeenstr@redhat.com)
- cli: Config refactoring (vfeenstr@redhat.com)
- cli: Fixed paramiko host key check (vfeenstr@redhat.com)
- cli: Allow to use different user names, identity files etc in migrate-machine
  (vfeenstr@redhat.com)
- cli: Fixed more parts of the SSH code (vfeenstr@redhat.com)
- cli: Add find_machine support for SSH discovery (vfeenstr@redhat.com)
- cli: Code fixes from the refactoring (vfeenstr@redhat.com)
- cli: Refactored out Vagrant SSH detection to driver (vfeenstr@redhat.com)
- cli: SSH machine implementation (vfeenstr@redhat.com)
- note more explicitely why to use sudo to start the VMs (pcahyna@redhat.com)
- Fix the demo instructions: - demo/start_vms.sh is no more (since
  a1e8cbbf37c986fedcb66b152457394cc88f09de) - one should start the VMs using
  sudo, as leapp-tool is run under sudo as well   and it should be run under
  the same user as the VM provisioning (it accesses   the Vagrant cache of the
  user to find the domains, see also the commit   message for rev.
  59c9c23b627dfc48034715408b6d09c88bc9e665) - since rev.
  6e19c02f0d9378e0755870101842329a42289002, the '--user vagrant'   parameter is
  required (the default for ssh user was changed to the current   user).
  (pcahyna@redhat.com)
- Build the RPM in pre-merge CI (ncoghlan@gmail.com)
- Fix tito build errors (ncoghlan@gmail.com)
- missing pub key for centos6-drools (mfranczy@redhat.com)
- partially refactored migrate machine code (root@mgazdik-
  leapp.usersys.redhat.com)
- tests are now verifying if the execution failed because of port collisions
  defined by user (root@mgazdik-leapp.usersys.redhat.com)
- adding tests [WIP] (root@mgazdik-leapp.usersys.redhat.com)
- Stop execution on user mapped port collision - initial commit
  (mgazdik@redhat.com)
- get list by logic operator (mfranczy@redhat.com)
- Defined portlist for port scanner and re-defined port-map based on portlist
  (root@mgazdik-leapp.usersys.redhat.com)
- remove only default ports (mfranczy@redhat.com)
- corrected error message in port_scan and added check for user_excluded_ports
  (mgazdik@redhat.com)
- --tcp-port as mandatory param, remove default forwarded ports
  (mfranczy@redhat.com)
- removed forgotten comments (mgazdik@redhat.com)
- removed self check for protocol lists (mgazdik@redhat.com)
- corrected docstrings (mgazdik@redhat.com)
- corrected docstrings (mgazdik@redhat.com)
- Relax the migration timing for CI again (ncoghlan@gmail.com)
- Restore & fix destroy-containers subcommand (ncoghlan@gmail.com)
- Revert "Don't test removed destroy-containers subcommand"
  (ncoghlan@gmail.com)
- enabled shallow scan by default (root@mgazdik-leapp.usersys.redhat.com)
- modified httpd-stateless test due to the same reasons as the portmapping
  tests (the machines need to be fresh so predict the new port mapping)
  (root@mgazdik-leapp.usersys.redhat.com)
- modified tests, so they reset vms before they start (mgazdik@redhat.com)
- Refactor storage path handling (ncoghlan@gmail.com)
- Update comment to match task structure (ncoghlan@gmail.com)
- Don't test removed destroy-containers subcommand (ncoghlan@gmail.com)
- Fix various issues in macrocontainer removal (ncoghlan@gmail.com)
- Corrected one test, added new one and code can now detect collisions with
  user mapped pots (root@mgazdik-leapp.usersys.redhat.com)
- Add trailing newline (ncoghlan@gmail.com)
- Split out target system cleanup (ncoghlan@gmail.com)
- corrected tests and switched source:target ports in user port map building
  procedure [WIP] (root@leapp.mgnet.cz)
- Added port exclusion [WIP] (root@leapp.mgnet.cz)
- added --no-tcp-port argument (root@leapp.mgnet.cz)
- PortMap is now subclass of OrderedDict [WIP] (root@mgazdik-
  leapp.usersys.redhat.com)
- initial commit with PortMap class replacing OrderedDict [WIP]
  (mgazdik@redhat.com)
- remove unused var (mfranczy@redhat.com)
- fixed source_cfg (mfranczy@redhat.com)
- add cfg for source (mfranczy@redhat.com)
- added port_map init function (mgazdik@redhat.com)
- machine context (mfranczy@redhat.com)
- modified default mapping test in order to accomodate the port conflict resolv
  behavior (root@mgazdik-leapp.usersys.redhat.com)
- Added basic port conflict resolver (root@mgazdik-leapp.usersys.redhat.com)
- Added info for user about migrated ports (root@mgazdik-
  leapp.usersys.redhat.com)
- solved switch ports + modified test accordingly (root@mgazdik-
  leapp.usersys.redhat.com)
- if it's impossible to freeze fs then stop migration - for example perm denied
  (mfranczy@redhat.com)
- remove unnecessary function from integration test (mfranczy@redhat.com)
- fixed int tests (mfranczy@redhat.com)
- int tests (mfranczy@redhat.com)
- clean code (mfranczy@redhat.com)
- fixed closing perm connection (mfranczy@redhat.com)
- parameter name changed in port-inspect from ip -> address (root@mgazdik-
  leapp.usersys.redhat.com)
- added error handling in migration scan (mgazdik@redhat.com)
- catch exceptions (mfranczy@redhat.com)
- rsync as alternative for virt-tar-out (mfranczy@redhat.com)
- help for tcp-port difined properly (marcel@marcel.mg-net.cz)
- added port override test (root@mgazdik-leapp.usersys.redhat.com)
- Added new tests for default autodetection (root@mgazdik-
  leapp.usersys.redhat.com)
- tweaking of the default port detection test steps (root@mgazdik-
  leapp.usersys.redhat.com)
- defined test for getting default ports (root@mgazdik-
  leapp.usersys.redhat.com)
- Added port detection test (WIP) (root@mgazdik-leapp.usersys.redhat.com)
- minor changes (mgazdik@redhat.com)
- Changed dicts back to arrays since it doesn't require modification of MC +
  minotr tweaks (mgazdik@redhat.com)
- Changed array of ports to dict (mgazdik@redhat.com)
- Disabled --udp-port option, but implementation is being kept in the code,
  ports can be overriden and added by user (mgazdik@redhat.com)
- Added --udp-port option, continuing the work on re-mapping
  (mgazdik@redhat.com)
- fixed some issues, odded port remappnig (mgazdik@redhat.com)
- No preset user when installed via RPM (ncoghlan@gmail.com)
- Use hyphens in config setting names (ncoghlan@gmail.com)
- Note Splinter RFE for 'Enabled?' check (ncoghlan@gmail.com)
- Remove hardcoded user from Cockpit plugin (ncoghlan@gmail.com)
- Add test case for migration through the plugin (ncoghlan@gmail.com)
- Make validity check more self-explanatory (ncoghlan@gmail.com)
- Only use `sudo vagrant` when not root (ncoghlan@gmail.com)
- Added basic structure of port override (mgazdik@redhat.com)
- Modified migrate machine, so the port-inspect can be tested and new params as
  well (mgazdik@redhat.com)
- Modified migrate machine, so the port-inspect can be tested and new params as
  well (mgazdik@redhat.com)
- cockpit: Fix empty initial input scan attempt (vfeenstr@redhat.com)
- cockpit: Fix toggle bug - did not hide input when custom gets unchecked
  (vfeenstr@redhat.com)
- Restore ability to run tests as non-root user (ncoghlan@gmail.com)
- Added _port_scan function and modified port-inspect to use it
  (mgazdik@redhat.com)
- cli: Add back accidentally removed line (vfeenstr@redhat.com)
- cli: Apply custom target support to destroy containers (vfeenstr@redhat.com)
- cli: Apply custom target support to migrate-machine (vfeenstr@redhat.com)
- Added Marcel Gazdik into list of authors (mgazdik@redhat.com)
- cockpit: Add missing semicolon (vfeenstr@redhat.com)
- cockpit: Simply and improve functionality (vfeenstr@redhat.com)
- cockpit: Add custom target address support (vfeenstr@redhat.com)
- cli: Allow FQDN to be used as argument for port-inspect (vfeenstr@redhat.com)
- added /CONTRIBUTING.rst symlink to contributing.rst (mgazdik@redhat.com)
- changed getting started link (mgazdik@redhat.com)
- Replaced content of README.md files with links to the readthedocs pages
  (mgazdik@redhat.com)
- Added Marcel Gazdik to the reviewers list & alph. sorted the list
  (mgazdik@redhat.com)
- removed wrong comment from contributing.rst (mgazdik@redhat.com)
- Amend the rationale for sticking with an older Selenium (ncoghlan@gmail.com)
- Check for failure to load the login page (ncoghlan@gmail.com)
- Enable Cockpit socket activation (ncoghlan@gmail.com)
- Remove spurious trailing slash (ncoghlan@gmail.com)
- Remove unintended task separator (ncoghlan@gmail.com)
- Quote template expression correctly (ncoghlan@gmail.com)
- CI: Add dev symlink for use by Cockpit plugin (ncoghlan@gmail.com)
- Document the Selenium compatibility issue (ncoghlan@gmail.com)
- Remove outdated check for geckodriver (ncoghlan@gmail.com)
- Configure CI for UI testing (ncoghlan@gmail.com)
- Enable Cockpit integration testing (ncoghlan@gmail.com)
- Clarify failure when machines are missing (ncoghlan@gmail.com)
- Added GAZDOWN user into integration-tests (mgazdik@redhat.com)
- added /CONTRIBUTING.rst symlink to contributing.rst (mgazdik@redhat.com)
- changed getting started link (mgazdik@redhat.com)
- Replaced content of README.md files with links to the readthedocs pages
  (mgazdik@redhat.com)
- Added Marcel Gazdik to the reviewers list & alph. sorted the list
  (mgazdik@redhat.com)
- removed wrong comment from contributing.rst (mgazdik@redhat.com)
- Amend the rationale for sticking with an older Selenium (ncoghlan@gmail.com)
- Check for failure to load the login page (ncoghlan@gmail.com)
- Enable Cockpit socket activation (ncoghlan@gmail.com)
- Remove spurious trailing slash (ncoghlan@gmail.com)
- Remove unintended task separator (ncoghlan@gmail.com)
- Quote template expression correctly (ncoghlan@gmail.com)
- CI: Add dev symlink for use by Cockpit plugin (ncoghlan@gmail.com)
- Document the Selenium compatibility issue (ncoghlan@gmail.com)
- Remove outdated check for geckodriver (ncoghlan@gmail.com)
- Configure CI for UI testing (ncoghlan@gmail.com)
- Enable Cockpit integration testing (ncoghlan@gmail.com)
- Clarify failure when machines are missing (ncoghlan@gmail.com)
- Be pythonic and follow pep8 (vfeenstr@redhat.com)
- Add package listing for non-shallow scans (vfeenstr@redhat.com)
- Name changed from LeApp-To back to LeApp (mgazdik@redhat.com)
- Drop creation of ovirt-guest-agent channels (vfeenstr@redhat.com)
- Drop ovirt-guest-agent ansible role usage (vfeenstr@redhat.com)
- TRELLO#104 Inspect source machine only using ssh (vfeenstr@redhat.com)
- WIP install steps - the vagrant modules build procedure must be tested
  (mgazdik@redhat.com)
- WIP on install steps for CentOS7, RHEL7, Fedora 25 (mgazdik@redhat.com)
- removed emoticons (mgazdik@redhat.com)
- added demo documentation (mgazdik@redhat.com)
- Changed project name Leapp -> LeApp-To (mgazdik@redhat.com)
- added integration tests and linked with contributing (mgazdik@redhat.com)
- added contributing (mgazdik@redhat.com)
- TRELLO#97 - Use direct libguestfs backend to avoid libvirt disk image
  relabeling (vfeenstr@redhat.com)
- content polishing (mgazdik@redhat.com)
- modified content in multiple pages, added content into leapp tool
  (mgazdik@redhat.com)
- Updated docs for RPM usage (vfeenstr@redhat.com)
- added forgoten comment (mgazdik@redhat.com)
- changed theme to RTD (mgazdik@redhat.com)
- changed README.md in centos-ci and / and added link to RTD
  (mgazdik@redhat.com)
- changed order in menu (mgazdik@redhat.com)
- added leapp-tool CLI command page and ui page (mgazdik@redhat.com)
- initial commit of centosci and geting started pages (mgazdik@redhat.com)
- initial Sphinx setup comit (mgazdik@redhat.com)
- Rephrase README, Fix cockpit (jsycha@redhat.com)
- Fully resolve merge conflict (ncoghlan@gmail.com)
- Declare sshpass dependency in RPM spec (ncoghlan@gmail.com)
- Use updated parameter name (ncoghlan@gmail.com)
- Install sshpass from EPEL for --ask-pass testing (ncoghlan@gmail.com)
- port-scan --shallow - integration tests (mfranczy@redhat.com)
- Finish reverting partial edit (ncoghlan@gmail.com)
- Support --ask-pass option in CLI (ncoghlan@gmail.com)
- fixed tests (mfranczy@redhat.com)
- remove whitespaces (mfranczy@redhat.com)
- fixed integration tests (mfranczy@redhat.com)
- remove console.log(s) (mfranczy@redhat.com)
- get info about products which are listening on discovered ports
  (mfranczy@redhat.com)
- user can choose port manually (mfranczy@redhat.com)
- use fast port scan to collect information about used ports
  (mfranczy@redhat.com)
- fast port scan (mfranczy@redhat.com)
- syntax styling (mgazdik@redhat.com)
- REDME.md modifications (root@mgazdik-leapp.usersys.redhat.com)
- Cockpit: Show version info (vfeenstr@redhat.com)
- Cockpit: configuration of tool path (vfeenstr@redhat.com)
- vagrant stop command is halt (vfeenstr@redhat.com)
- Fix ansible roles path broken in #109 (vfeenstr@redhat.com)
- NOJIRA: ammending README as per PR review (vmindru@redhat.com)
- Remove trailing semi-colon from ssh-agent settings (ncoghlan@gmail.com)
- Leaving the documented tool path in cockpit and fix it during rpm creation
  for RPM installations (vfeenstr@redhat.com)
- Start ssh-agent in integration tests when necessary (ncoghlan@gmail.com)
- NOJIRA: ammending README as per PR review (vmindru@redhat.com)
- Fix tool path in cockpit (vfeenstr@redhat.com)
- Fixed spec file changelog and removed duplicate entries due to tito misusage
  (vfeenstr@redhat.com)
- Actually test ssh-agent based authentication (ncoghlan@gmail.com)
- Set return code for destroy-containers command (ncoghlan@gmail.com)
- Consolidate LeApp id management in integration tests (ncoghlan@gmail.com)
- Update test docs for new feature & steps (ncoghlan@gmail.com)
- Allow use of default SSH credentials in CLI (ncoghlan@gmail.com)
- TRELLO#70: ammend docs in README (vmindru@redhat.com)
- TRELLO#70: incorporate changes from #105 (vmindru@redhat.com)
- TRELLO#70: ading clean start action, merging all scripts into one
  (vmindru@redhat.com)
- Using a spec file for specifying required dependencies to run the demo
  (vfeenstr@redhat.com)


* Mon May 08 2017 Vinzenz Feenstra <vfeenstr@redhat.com> 0.0.1-5
- Touch non existing file workaround not necessary anymore files have been
  already added (vfeenstr@redhat.com)

* Fri May 05 2017 Vinzenz Feenstra <vfeenstr@redhat.com> 0.0.1-4
- We also need virsh (vfeenstr@redhat.com)
- The license choosen for LeApp is now LGPLv2+ (vfeenstr@redhat.com)
- Missing nmap dependency added (vfeenstr@redhat.com)
- Drop obsolete __vagrant_ssh_checkoutput (vfeenstr@redhat.com)
- Drop unnecessary build requires (vfeenstr@redhat.com)

* Fri May 05 2017 Vinzenz Feenstra <vfeenstr@redhat.com> 0.0.1-3
- Fixed el 7 builds (vfeenstr@redhat.com)

* Fri May 05 2017 Vinzenz Feenstra <vfeenstr@redhat.com> 0.0.1-2
- new package built with tito

* Thu May 04 2017 Vinzenz Feenstra <evilissimo@redhat.com> - 0.0.1-1
- Initial

