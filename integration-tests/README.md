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

    $ pipenv --three && pipenv install

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

## Writing new tests

New feature definitions go in the ["features"](./features) subdirectory.

New step definitions go in the ["features/steps"](./features.steps)
subdirectory, and use the
["hamcrest"](https://pyhamcrest.readthedocs.io/en/latest/tutorial/)
library to define behavioural expectations.

The available custom steps are not yet documented - look at the sexisting
feature and step definitions for examples.