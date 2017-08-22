Contributing to LeApp
=====================

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing effectively to LeApp,
which is hosted in the `LeApp-To Organization <https://github.com/leapp-to/>`_ on Github.
These guidelines are expected to change over time as the needs of the project
evolve, so feel free to propose changes to this document in a pull request -
it's a lot easier to discuss a specific proposed update than it is general
principles.

Submitting Issues
^^^^^^^^^^^^^^^^^

* All elements of the current version (documentation, CLI, demonstration Cockpit plugin, 
  integration tests) are maintained in the `leapp repo <https://github.com/leapp-to/leapp>`_, 
  so any issues should be filed there regardless of the component they relate to

Submitting a Pull Request
^^^^^^^^^^^^^^^^^^^^^^^^^

*Note: Every PR should have at least one review from at least one of the Core Reviewers.*

Core Reviewers are:

* Marcel Gazdik
* Marcin Franczyk
* Nick Coghlan
* Pavel Odvody
* Veaceslav Mindru
* Vinzenz Feenstra

Before you submit your pull request consider the following guidelines:

* Fork the repository and clone your fork
* Make your changes in a new git branch:
 
     ``git checkout -b bug/my-fix-branch master``

* Create your patch, **ideally including appropriate test cases**
* Include documentation that either describe a change to a behavior or the changed capability to an end user
* Commit your changes using **a descriptive commit message**. If you are fixing an issue please include something like 'this closes issue #xyz'
* Make sure your tests pass! We use Jenkins CI for our automated testing
* Push your branch to GitHub:

    ``git push origin bug/my-fix-branch``

* When opening a pull request, select the `master` branch as a base.
* Mark your pull request with **[WIP]** (Work In Progress) to get feedback but prevent merging (e.g. [WIP] Update CONTRIBUTING.md)
* If we suggest changes then:
    * Make the required updates
    * Push changes to git (this will update your Pull Request):
        * You can add new commit
        * Or rebase your branch and force push to your Github repository: ::

            git rebase -i master
            git push -f origin bug/my-fix-branch

That's it! Thank you for your contribution!

Merge Rules
-----------

* Include unit or integration tests for the capability you have implemented
* Integration tests should use "ensure_fresh=no" when setting up VMs (if
  "ensure_fresh=yes" seems to be needed, it's a sign that there's a missing
  cleanup task in the Ansible provisioning playbook for that VM definition)
* Include documentation for the capability you have implemented
* If you are fixing an issue, include the issue number you are fixing
* Python code should follow `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ conventions

Git Commit Messages
^^^^^^^^^^^^^^^^^^^

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Reference issues and pull requests liberally

Component specific details
^^^^^^^^^^^^^^^^^^^^^^^^^^


:doc:`leapp-tool` CLI
---------------------

* The `leapp-tool` CLI is written in the Python 3 compatible subset of Python 2.7
* All CLI dependencies must be available and installable as RPMs
* COPR repositories will be used for any dependencies not available by default
  in RHEL/CentOS
* Use `sudo` for operations that must be executed with elevated privileges
* The integration tests install and run the CLI under Python 2.7 on CentOS 7,
  but don't currently check Python 3 compatibility

Integration tests
^^^^^^^^^^^^^^^^^

* The integration tests run under Python 3.5 using the `behave` framework
* Integration testing VMs are managed using Vagrant and configured via Ansible
* On CentOS/RHEL 7, the integration tests require the Vagrant and Python 3.5
  SCLs
* Test dependencies may be installed as RPMs, Vagrant plugins, or through
  `pipenv` (i.e. Python packages)
* All test dependencies should be pinned to a specific version, so changes
  aren't unexpectedly introduced into the CI environment
* When new feature files, step files, or context attributes are defined, add
  a corresponding entry to the
  :doc:`integration tests <integration-tests>`
* see the :doc:`integration tests <integration-tests>` for more
  details

### Demonstration Cockpit plugin

* The demonstration Cockpit plugin is currently written in JavaScript & raw HTML
* It should run correctly when used in Firefox on RHEL/CentOS 7 (this
  requirement is not currently checked in the CI environment, but can be
  tested locally by running `behave --wip`)

Setting up a development environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This guide assumes that you are running Fedora. Make sure to translate the commands if you are running a different distribution.

Installing leapp
----------------

First of all, let's install the `leapp-tool`. By the end of this sub-section, we'll be able to run a migration from the command line.

We start off by cloning the repository. We assume that you keep your source files in `~/src`:
::

    mkdir ~/src; cd ~/src
    git clone https://github.com/leapp-to/leapp.git
    cd ~/src/leapp

Run the following command to install all dependencies needed by the `leapp-tool`:
::

    sudo dnf builddep leapp.spec

We'll use `pipsi` to install `leapp-tool` from our repository:
::

    pipsi install --python /usr/bin/python2.7 $PWD/src
    sudo ln -s $HOME/.local /opt/leapp

Create the directory where the imported macrocontainers will be stored:
::

    sudo mkdir -p /var/lib/leapp/macrocontainers/

By now you should be able to run the tool successfully:
::

	$ sudo /opt/leapp/bin/leapp-tool --version
	leapp-tool 0.1

Running a demo
-----------------

In this sub-section we'll migrate a virtual machine to a container by using the command line. In order to do that, we first need a running virtual machine.

First, we need to install a set of specific packages to run the virtual machines:
::

	sudo dnf builddep demo/prototype-deps.spec

Then, chose one of the guest vagrant boxes in `demo/vmdefs/available` and create a symlink to `demo/vmdefs/enabled`. For example, let's assume we are going to migrate the `centos6-guest` box:
::

	ln -s $PWD/demo/vmdefs/available/centos6-guest $PWD/demo/vmdefs/enabled

Now, start the enabled box with:
::

	sudo demo/vmctl.sh provision

The last step necessary is to import the private key from the vagrant box. This key is necessary to move files around the source and target:
::

	ssh-add $PWD/demo/vmdefs/available/centos6-guest/.vagrant/machines/default/libvirt/private_key

Run the following command to make sure everything is set up correctly. Make sure to replace `192.168.121.66` by your box's IP address (tip: you can `vagrant ssh` into your box and check its address):
::

	sudo SSH_AUTH_SOCK=$SSH_AUTH_SOCK /opt/leapp/bin/leapp-tool migrate-machine -p --use-rsync -t 127.0.0.1 192.168.121.66 --target-user vagrant --source-user vagrant
	[
		[
			9022,
			22
		],
		(...)
	]

Set up leapp as a Cockpit plugin
--------------------------------

Make sure Cockpit is installed in your development machine:
::

	sudo dnf install cockpit
	sudo systemctl start cockpit

In the `leapp` source directory, run this command to install the plugin:
::

	ln -s $PWD/cockpit ~/.local/share/cockpit/leapp

Browse to http://localhost:9090 and log in with your user and password.

Just like in your dev machine, we need to import the box's private key, but now within Cockpit. To do that, click ``Terminal`` and execute:
::

	cd ~/src/leapp
	ssh-add demo/vmdefs/available/centos6-guest/.vagrant/machines/default/libvirt/private_key

Now you should be able to convert the vagrant box to a container. Click ``Import apps``, type the IP address of you vagrant box and click ``Find apps``. You should see a mapping of ports in the VM to ports in the container. Simply click ``Import`` and wait a few minutes for the process to finish.

You'll be able to see new container in the ``Containers`` link at the left panel.
