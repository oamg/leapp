Contributing to Leapp
=====================

First, thank you for taking your time to contribute to the project.

A set of guidelines for contributing effectively to Leapp
is hosted in the `Leapp-To Organization <https://github.com/leapp-to/>` on GitHub.
These guidelines are expected to change over time as the needs of the project
evolve, so propose changes to this document in pull requests, as it is easier to discuss a specific proposed
update than general principles.

Submitting Issues
^^^^^^^^^^^^^^^^^

* All elements of the current version (documentation, CLI, and 
  unit tests) are maintained in the `leapp repo <https://github.com/leapp-to/leapp>`, 
  so any issues should be filed there regardless of the component they relate to.

Submitting a Pull Request
^^^^^^^^^^^^^^^^^^^^^^^^^

*Note: Every pull request should have at least one review from the core reviewers.*

Core reviewers are:

* Fabio Bertinatto
* Marcel Gazdik
* Marcin Franczyk
* Pavel Odvody
* Vinzenz Feenstra

Before you submit your pull request, consider the following guidelines:

* Fork the repository and clone your fork.
* Make your changes in a new git branch:
 
     ``git checkout -b bug/my-fix-branch master``

* Create your patch, **ideally including appropriate test cases**.
* a Include documentation that either describes a change to the behavior, or a changed capability for end users.
* Commit your changes by using **a descriptive commit message**. If you are fixing a bug, include a line like
  'close a bug #xyz'.
* Make sure your tests pass. We use Jenkins CI for our automated testing.
* Push your branch to GitHub:

    ``git push origin bug/my-fix-branch``

* When opening a pull request, select the `master` branch as a base.
* Mark your pull request with **[WIP]** (Work In Progress) to get feedback, but prevent merging (for example,
  [WIP] Update CONTRIBUTING.md).

If we suggest changes, follow these rules:
------------------------------------------

* Make the required updates.
* Push changes to git (this will update your pull request). For that you can add a new commit or rebase your branch
  and force push to your GitHub repository like this: ::

    git rebase -i master
    git push -f origin bug/my-fix-branch


Merge Rules
-----------

* Include unit tests for the capability you have implemented.
* Include a documentation for the capability you have implemented.
* If you are fixing an issue, include the issue number you are fixing.
* Python code should follow the _`PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ conventions.

Git Commit Messages
^^^^^^^^^^^^^^^^^^^

* Use the imperative mood.
* Reference issues and pull requests liberally.


