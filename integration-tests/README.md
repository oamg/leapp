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

    $ pipenv install

## Running the tests

Once the environment is set up, the tests can be run via:

    $ pipenv run behave

To get a local shell with the testing environment active, run:

    $ pipenv shell

Once in the testing environment, the tests can be run just by
invoking `behave` directly.
