# Kernel modernization integration tests

This directory contains integration tests that check the expected results
of kernel modernization attempts given different starting scenarios.

* Test scenarios and expectations are defined using the Python
  [behave](http://pythonhosted.org/behave/) framework
* Local virtual machines for test cases are defined and configured
  using the
  [Ansible Python API](http://docs.ansible.com/ansible/dev_guide/developing_api.html)
* The integration testing environment itself is configured using
  [pipenv](https://pypi.python.org/pypi/pipenv)

## Setting up

Install `vagrant` and `vagrant-libvirt`:

    $ sudo dnf install vagrant vagrant-libvirt

And allow yourself passwordless access to VM management operations:

    $ sudo usermod -aG vagrant,libvirt $USER

You will need to log out and back in again, or start a new user
session with `su $USER`, to get the new group memberships to take
effect.

Install `pipenv` and the `pew` environment management tool:

    $ pip install --user pipsi
    $ pipsi install pew
    $ pipsi install pipenv

The above commands do a user level install of the "pip script installer",
and then install `pew` and `pipenv` into isolated virtual environments
for reliability of later updates. (`pew` needs to be installed separately
so `pipenv` sees only the command line interface instead of the Python API)

Once `pipenv` is installed, run the following to install the
integration testing environment:

    $ pipenv --three && pipenv install --dev

Note that while `leapp` itself will run under Python 2.7, the integration
tests require Python 3.

## Running the tests

To get a local shell with the testing environment active, run:

    $ pipenv shell

Once in the testing environment, the tests can be run by invoking
`behave` test runner directly from the `integration-tests`
directory:

    $ behave

The tests require passwordless access to `vagrant`, and passwordless `sudo`
access to `leapp-tool` (alternatively, they will require interactive
password entry during the test).

## Writing new test scenarios

New feature and scenario definitions go in the ["features"](./features)
subdirectory.

Refer to the
[behave tutorial](https://pythonhosted.org/behave/tutorial.html#feature-files)
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

If a new test scenario doesn't align with any of the existing features, then
an appropriate new feature should also be defined.

To get a list of the available steps and their documentation, run:

    $ behave --steps-catalog

The `@wip` tag can be used to mark a work-in-progress scenario as follows:

    @wip
    Scenario: the scenario you are adding/changing
         Given ...
         When ...
         Then ...

The tagged scenarios can then be run with the
[`--wip`](https://pythonhosted.org/behave/behave.html#cmdoption-w) option:

    $ behave --wip

In addition to only running the appropriately tagged scenarios, this option
runs behave in a mode that switches off the default stdout and logging capture,
and stops immediately at the first failure.

Not-yet-implemented scenario definitions can also be shared by marking them
with the `@skip` tag:

    @skip
    Scenario: a not-yet-implemented scenario
         Given ...
         When ...
         Then ...

This allows an initial draft of the desired behaviour to be specified and
merged prior to starting work on the implementation of the new behaviour and
any new test steps required.

## Adding new steps to the steps catalog

New step definitions go in the ["features/steps"](./features/steps)
subdirectory, and use the
["hamcrest"](https://pyhamcrest.readthedocs.io/en/latest/tutorial/)
library to define behavioural expectations.

Refer to the
[behave tutorial](https://pythonhosted.org/behave/tutorial.html#python-step-implementations)
for an introduction to the process of writing new steps, and the options
available for passing data from test scenarios to the individual step functions.

The following step categories are currently defined:

* `cockpit_demo.py`: Steps related specifically to testing the demonstration
  Cockpit plugin
* `destroy_containers.py`: Steps related specifically to the `destroy-container`
  subcommand
* `list_machines.py`: Steps related specifically to the `list-machines`
  subcommand
* `port_inspect.py`: Steps related specifically to the `port-inspect`
  subcommand
* `common.py`: Steps that are generally useful and don't fit into one of the
  more specific categories. This includes steps relating to the primary
  `migrate-machine` subcommand.

## Test context helpers for writing step definitions

All step definitions receive the current `behave` context as their first
parameter, and the [environment file](./features/environment.py) adds a few
useful attributes for use in step implementations:

* `BASE_REPO_DIR`: a `pathlib.Path` instance referring to the base of the
  prototype repo

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


## Adding new helpers to the test context

Helper functions and classes for a single set of steps can be included
directly in the Python file defining the steps.

Helpers that are shared amongst multiple sets of steps should be defined in
the ["features/leapp_testing"](./features/leapp_testing) package, and then
added to the test context using one of the hooks in the
[environment file](./features/environment.py).


## Debugging the test VMs

From the `integration-tests` directory, an instance of each of the integration
test VMs can be started by running:

    $ start_vms.sh

This script iterates over all the subdirectories of `integration-tests/vmdefs`
and runs `vagrant up --provision`.

To access a particular VM, switch to the corresponding directory and run:

    $ vagrant ssh

This will log you into the VM as the `vagrant` user, with `root` access
available via `sudo` (no password required).
