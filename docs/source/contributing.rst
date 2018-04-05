Contributing to Leapp
=====================

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing effectively to Leapp,
which is hosted in the `Leapp-To Organization <https://github.com/leapp-to/>` on Github.
These guidelines are expected to change over time as the needs of the project
evolve, so feel free to propose changes to this document in a pull request -
it's a lot easier to discuss a specific proposed update than it is general
principles.

Submitting Issues
^^^^^^^^^^^^^^^^^

* All elements of the current version (documentation, CLI, demonstration Cockpit plugin, 
  integration tests) are maintained in the `leapp repo <https://github.com/leapp-to/leapp>`, 
  so any issues should be filed there regardless of the component they relate to

Submitting a Pull Request
^^^^^^^^^^^^^^^^^^^^^^^^^

*Note: Every PR should have at least one review from at least one of the Core Reviewers.*

Core Reviewers are:

* Fabio Bertinatto
* Marcel Gazdik
* Marcin Franczyk
* Pavel Odvody
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

