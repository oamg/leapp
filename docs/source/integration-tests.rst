Integration tests
=================

Legacy Application import integration tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This directory contains integration tests that check the expected results
of kernel modernization attempts given different starting scenarios.

* Test scenarios and expectations are defined using the Python
  `behave <http://pythonhosted.org/behave/>`_ framework
* Local virtual machines for test cases are defined and configured
  using the
  `Ansible Python API <http://docs.ansible.com/ansible/dev_guide/developing_api.html>`_
* The integration testing environment itself is configured using
  `pipenv <https://pypi.python.org/pypi/pipenv>`_

Setting up the host system
--------------------------

Install `ansible`, `docker`, `vagrant`, and `vagrant-libvirt`: ::

    sudo dnf install docker vagrant vagrant-libvirt

And allow yourself passwordless access to container and VM management
operations: ::

    sudo usermod -aG docker,vagrant,libvirt $USER

You will need to log out and back in again, or start a new user
session with `su $USER`, to get the new group memberships to take
effect.

Note: running `docker` without `sudo` can bypass audit controls, so if that's
a potential problem, set up a dedicated system for running the LeApp tests

Setting up a local Python environment
-------------------------------------

Install `pipenv` and the `pew` environment management tool: ::

    pip install --user pipsi
    pipsi install pew
    pipsi install pipenv

The above commands do a user level install of the "pip script installer",
and then install `pew` and `pipenv` into isolated virtual environments
for reliability of later updates. (`pew` needs to be installed separately
so `pipenv` sees only the command line interface instead of the Python API)

Once `pipenv` is installed, run the following to install the
integration testing environment: ::

    pipenv --three && pipenv install --dev

Note that while `leapp` itself will run under Python 2.7, the integration
tests require Python 3.

Running the tests
-----------------

To get a local shell with the testing environment active, run: ::

    pipenv shell

Once in the testing environment, the tests can be run by invoking
`behave` test runner directly from the `integration-tests`
directory: ::

    behave

The tests require passwordless access to `vagrant`, and passwordless `sudo`
access to `leapp-tool` (alternatively, they will require interactive
password entry during the test).

Running the tests without `pipenv`
----------------------------------

Using a dedicated Python virtual environment may not be necessary if some other
form of environment separation is already in use (e.g. the use of the Python
3.5 SCL in the CI configuration).

For such cases, a generated `requirements.txt` file is kept in the
`integrations-tests` directory, allowing a testing environment to be configured
with the following commands::

    pip install --user pipsi
    pip install -r integration-tests/requirements.txt

Running the tests against an already installed RPM
--------------------------------------------------

By default, the tests use `pipsi` and automatically generated symlinks to
test against the CLI and Cockpit plugin located in the git clone containing
the test suite.

This behaviour can be overridden by setting the ``LEAPP_TEST_RPM`` environment
variable when running the tests::

    LEAPP_TEST_RPM=1 behave

Any non-empty string will cause the tests to expect LeApp to already be
installed, and to run against that installed version.


Adding new test suite dependencies
----------------------------------

Test suite dependencies are listed under `[dev-packages]` in `Pipfile`. When
the dependencies are updated, then both `Pipfile.lock` and
`integration-tests/requirements.txt` need to be regenerated:

    pipenv lock
    pipenv lock --requirements | sort > integration-tests/requirements.txt

Note: due to a current pipenv limitation, regenerating the lock files currently
reformats `Pipfile`, stripping all comments in the process. As a workaround,
it's advisable to check in the `Pipfile` changes, regenerate the lock files,
checkout the previously commited `Pipfile`, and then amend the commit to include
the regenerated lock files.

Writing new test scenarios
--------------------------

New feature and scenario definitions go in the `"features" <https://github.com/leapp-to/leapp/tree/master/integration-tests/features>`_
subdirectory.

Refer to the
`behave tutorial <https://pythonhosted.org/behave/tutorial.html#feature-files>`_
for a description of the format of feature files, and the recommended structure
to use when defining new test scenarios.

The following features are currently defined:

* `cockpit-demo.feature`: expected behaviour of the demonstration Cockpit
  plugin
* `destroy-containers.feature`: expected behaviour of the `destroy-container`
  subcommand
* `httpd-stateless.feature`: expected behaviour of the `migrate-machine`
  subcommand when migrating stateless applications running under Apache `httpd`
* `list-machines.feature`: expected behaviour of the `list-machines` subcommand
* `port-inspect.feature`: expected behaviour of the `port-inspect` subcommand
* `remote-authentication.feature`: end-to-end testing of available remote
  authentication options

If a new test scenario doesn't align with any of the existing features, then
an appropriate new feature should also be defined.

To get a list of the available steps and their documentation, run: ::

    behave --steps-catalog

The `@wip` tag can be used to mark a work-in-progress scenario as follows: ::

    @wip
    Scenario: the scenario you are adding/changing
         Given ...
         When ...
         Then ...

The tagged scenarios can then be run with the
`"--wip" <https://pythonhosted.org/behave/behave.html#cmdoption-w>`_ option: ::

    behave --wip

In addition to only running the appropriately tagged scenarios, this option
runs behave in a mode that switches off the default stdout and logging capture,
and stops immediately at the first failure.

Not-yet-implemented scenario definitions can also be shared by marking them
with the `@skip` tag: ::

    @skip
    Scenario: a not-yet-implemented scenario
         Given ...
         When ...
         Then ...

This allows an initial draft of the desired behaviour to be specified and
merged prior to starting work on the implementation of the new behaviour and
any new test steps required.

Some scenarios may be slow or encounter other problems when run as a non-root
user. These can be marked with ``@root_recommended`` and will then only be
executed when either that tag is specified, or else the test suite is running as
the root user (as it does in pre-merge CI).

To run these tests as a regular user for local testing of a particular feature
without running the whole test suite as root, specify::

    behave -i <feature-of-interest> --tags root_recommended

Setting up VMs for test scenarios
---------------------------------

Most test scenarios will include a VM setup step along the following lines::

   Given the local virtual machines:
         | name       | definition          | ensure_fresh |
         | app-source | centos6-guest-httpd | no           |
         | target     | centos7-target      | no           |

Configuration of these VMs is handled in the following ways:

* through the Vagrant file
  (``/integration-tests/vmdefs/<definition>/Vagrantfile``)
* through the Ansible provisioning playbook
  (``/integration-tests/vmdefs/<definition>/ansible/playbook.yml``)
* through additional setup steps in the test scenario itself

For checked in tests, the ``ensure_fresh`` setting should always be ``no``, and
the Ansible provisioning playbook for the VM definition should cover everything
needed to ensure that the VM is in a known-good state for running test
scenarios. This allows a single VM instance for each VM definition to be shared
not only between test scenarios, but also between different test *runs*, saving
around 3-5 minutes of test execution time for each VM destruction and recreation
cycle avoided.

For development and test debugging purposes, the ``ensure_fresh` setting can be
changed to ``yes``. This means that instead of just re-running the Ansible
provisioning playbook when a suitable VM instance already exists and halting
the VM instance when the scenario ends, the tests will instead destroy any
existing instance, create a completely fresh one, and then destroy that fresh
instance when the scenario ends. This is particularly helpful when writing
the initial ``Vagrantfile`` for a new VM definition, but can also be beneficial
when attempting to determine if a test failure may be due to a missing cleanup
step in the Ansible provisioning playbook.

Most test helpers that accept a declared VM name as input also accept
`"localhost"` to refer to the machine actually running the tests.

Adding new steps to the steps catalog
-------------------------------------

New step definitions go in the `"features/steps" <https://github.com/leapp-to/leapp/integrations-tests/features/steps>`_
subdirectory, and use the
`"hamcrest" <https://pyhamcrest.readthedocs.io/en/latest/tutorial/>`_
library to define behavioural expectations.

Refer to the
`behave tutorial <https://pythonhosted.org/behave/tutorial.html#python-step-implementations>`_
for an introduction to the process of writing new steps, and the options
available for passing data from test scenarios to the individual step functions.

The following step categories are currently defined:

* `check_target.py`: Steps related specifically to testing the target suitability
  checks
* `cockpit_demo.py`: Steps related specifically to testing the demonstration
  Cockpit plugin
* `destroy_containers.py`: Steps related specifically to the `destroy-container`
  subcommand
* `port_inspect.py`: Steps related specifically to the `port-inspect`
  subcommand
* `remote_authentication.py`: Steps related specifically to testing the
  available remote authentication options
* `common.py`: Steps that are generally useful and don't fit into one of the
  more specific categories. This includes steps relating to the primary
  `migrate-machine` subcommand.

Test context helpers for writing step definitions
-------------------------------------------------

All step definitions receive the current `behave` context as their first
parameter, and the `environment file <https://github.com/leapp-to/leapp/tree/master/integration-tests/features/environment.py>`_ adds a few
useful attributes for use in step implementations:

* `BASE_REPO_DIR`: a `pathlib.Path` instance referring to the base of the
  leapp repo

* `BASE_TEST_DIR`: a `pathlib.Path` instance referring to the directory
  containing the integration tests

* `scenario_cleanup`: a `contextlib.ExitStack` instance that can be used to
  register cleanup operations to run in the `@after_scenario` hook

* `vm_helper`: a custom object for managing local VMs (see
  `VirtualMachineHelper` in the environment file for details)

* `cli_helper`: a custom object for working with the LeApp tool (see
  `ClientHelper` in the environment file for details)

* `http_helper`: a custom object for checking HTTP(S) responses (see
  `RequestsHelper` in the environment file for details)


Adding new helpers to the test context
--------------------------------------

Helper functions and classes for a single set of steps can be included
directly in the Python file defining the steps.

Helpers that are shared amongst multiple sets of steps should be defined in
the `"features/leapp_testing" <https://github.com/leapp-to/leapp/tree/master/integration-tests/features/leapp_testing>`_ package, and then
added to the test context using one of the hooks in the
`environment file <https://github.com/leapp-to/leapp/tree/master/integration-tests/features/environment.py>`_.


Debugging the test VMs
----------------------

From the `integration-tests` directory, an instance of each of the integration
test VMs can be started by running: ::

    start_vms.sh

This script iterates over all the subdirectories of `integration-tests/vmdefs`
and runs `vagrant up --provision`.

To access a particular VM, switch to the corresponding directory and run: ::

    vagrant ssh

This will log you into the VM as the `vagrant` user, with `root` access
available via `sudo` (no password required).
