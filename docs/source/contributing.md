# Contributing to the Leapp project

First, thank you for taking your time to contribute to the project.

The following is a set of guidelines for contributing effectively to the Leapp-related repositories
hosted under the `OS and Application Modernization Group organization <https://github.com/oamg/>`_
on GitHub.

## Submitting a Pull Request

Before you submit your pull request, consider the following guidelines:

* Fork the repository and clone your fork.
* Make your changes in a new git branch:

     ``git checkout -b bug/my-fix-branch master``

* Include documentation that either describe a change to a behavior or the changed capability to an end user.
* Commit your changes with message conforming to the `Git Commit Messages`_ guidelines.
* Include tests for the capability you have implemented.
* Make sure your tests pass. We use Jenkins CI for our automated testing.
* Push your branch to GitHub:

    ``git push --set-upstream origin bug/my-fix-branch``

* When opening a pull request, select the `master` branch as a base.
* Mark your pull request with **[WIP]** (Work In Progress) to get feedback, but prevent merging (for example,
  [WIP] Update CONTRIBUTING.rst).
* If you are fixing a GitHub issue, include the issue number you are fixing, e.g. 'Closes issue #xyz'.
* Description of the PR should clearly state what is being changed and the rationale for the change.

### If we suggest changes, follow these rules:

* Make the required updates.
* Push changes to git (this will update your pull request). For that you can add a new commit or rebase your branch
  and force push to your GitHub repository like this: ::

    git rebase -i master
    git push -f origin bug/my-fix-branch

### Merge Rules

* Every PR should have at least one code review before merging
* All CI tests should pass

## Git Commit Messages

* Write a descriptive commit message
* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* If you are fixing a GitHub issue, include something like 'Closes issue #xyz'
* For more best practices, read `How to Write a Git Commit Message <https://chris.beams.io/posts/git-commit/>`_

## Contact

In case of any question, contact us on the freenode.net IRC channel #leapp, or write the question as an issue on
GitHub.