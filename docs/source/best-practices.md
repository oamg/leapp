# Best Practices for actor development

## Follow the contribution guidelines

See the [contribution guidelines](contributing).

## Avoid running code on a module level

Despite the actors being written in Python, they are loaded beforehand to get all the meta-information from them. To
avoid slow downs during this load phase we ask you to not execute any code that is not absolutely necessary
on a module level. Simple, fast code with no side-effects is acceptable, for example constant definitions.

## Avoid certain global imports

On a module level, try to import only the Python Standard Library modules or modules provided by the Leapp framework.
Import any other module within your function or method. This has to do with possible slow down when loading repositories
by the leapp tool, and also to avoid unnecessary complications for our tests automation which needs to inspect the
actors beforehand.

## Use the snactor tool for development

The snactor tool helps you with creating the base layout of a new Leapp repository, and with creating boilerplates for
the repository artifacts like actors, models, tags, topics, and workflows. It also helps you with debugging as it is
able to execute individual actors.

See the [tutorial on basic usage of snactor](tutorials/first-actor).

## Move generic functionality to libraries

Part of your actor's functionality might end up being rather generic or abstract. In that case, consider converting it
to a shared library function. You can introduce it in one of these two places:

- The [Leapp Standard Library](leapp.libraries.stdlib)

  The most generic functionality which actors of any workflow can use, e.g. function for exectuting a shell command,
  should go to the [Leapp Standard Library](leapp.libraries.stdlib).
  For that, please submit proposals through issues or pull requests under the
  [leapp GitHub repository](https://github.com/oamg/leapp/).

- Leapp repository-level shared library

  The functionality that may be useful for other actor developers but its scope is limited to the workflow you are
  writing your actor for, e.g. for an OS in-place upgrade workflow, should go to the `<Leapp repository>/libraries`
  folder. In this case, we welcome your proposals under the
  [leapp-repository on GitHub](https://github.com/oamg/leapp-repository).

  Please note that the name of the library module in this case should be unique and contain
  the actor name. For example:
`repos/system_upgrade/common/actors/checkrhsmsku/libraries/checkrhsmsku.py`


## Discover standard library functions

Before implementing functionality for your actor, browse through the available functionality provided by:

- the [Leapp Standard Library](https://github.com/oamg/leapp/tree/main/leapp/libraries/stdlib/),
- the shared library of your Leapp repository (`<Leapp repository>/libraries` folder).

These libraries contain functions that may satisfy your needs. Using them can save you time, lower code complexity and
help avoiding duplicate code. Improvement proposals for the library functions are welcome.

## Prefer using stdlib functions over shell commands

Sources of external functionality to be used in your actor in order of preference:

1. the [Leapp Standard Library](https://github.com/oamg/leapp/tree/main/leapp/libraries/stdlib/)
2. the [Python Standard Library](https://docs.python.org/3/library/index.html)
3. shell commands

Examples:

- Prefer `os.symlink` over `ls -s`
- Prefer `os.remove` over `rm`

There might be a valid reason for calling a shell command instead of a standard library function, e.g. the Python's
`shutil.copyfile` is not able to retain all of the file attributes, as opposed to shell's `cp --preserve`.

## Utilize messages produced by existing actors

As with the Leapp Standard Library mentioned above, it may be beneficial for you to skim through the actors already in
place in the [leapp-repository](https://github.com/oamg/leapp-repository). You might be interested in the messages they
produce, for example:

- [SystemFactsActor](https://github.com/oamg/leapp-repository/blob/main/repos/system_upgrade/common/actors/systemfacts/actor.py) -
  information about kernel modules, yum repos, sysctl variables, users, firewall, SELinux, etc.
- [RpmScanner](https://github.com/oamg/leapp-repository/blob/main/repos/system_upgrade/common/actors/rpmscanner/actor.py) -
  list of installed packages
- [StorageScanner](https://github.com/oamg/leapp-repository/blob/main/repos/system_upgrade/common/actors/storagescanner/actor.py) -
  storage information

In case you find any message of the existing actors to be incorrect, incomplete or misleading, we encourage you to
improve the respective actors.

## Write unit testable code

Write all the actor’s logic in the actor’s private library in order to be able to write unit tests for each of the
function. It is not currently possible to unit test any method or function in the _actor.py_. Then, ideally, the
`actor.process()` should contain only calling an entry point to the actor's library. To create an actor’s library,
create _libraries_ folder in the actor’s folder and in there create an arbitrarily named python file, e.g. _{actor_name}.py_.

_myactor/actor.py_:

```python
from leapp.libraries.actor.library import do_the_actor_thingy

class MyActor(Actor):
    # <snip>
    def process(self):
        do_the_actor_thingy(self)
```

_myactor/libraries/myactor.py_:

```python
def do_the_actor_thingy(actor):
    actor.log.debug("All the actor’s logic shall be outside actor.py")
```

For more about unit testing, see the [tutorial](tutorials/unit-testing).

## Do not introduce new dependencies

Ideally, actors shouldn't require any additional dependency on top of the dependencies already in the
[leapp](https://github.com/oamg/leapp/blob/main/packaging/leapp.spec) and
[leapp-repository](https://github.com/oamg/leapp-repository/blob/main/packaging/leapp-repository.spec) spec files,
which are, as of December 2018, just these:

- dnf
- python-six
- python-setuptools
- findutils

Rather than adding a new dependency to the spec file, detect in the actor if the package is installed and
if not, have a fallback option or skip the action you wanted to perform and report to the user that they should install
the package if they want to experience as smooth upgrade as possible.

If you're writing an actor for the RHEL 7 to RHEL 8 in-place upgrade workflow and you really need to have some package
installed, then the only acceptable packages to depend on are the the ones available in the minimal installation of
RHEL 7 (packages from the @core group + their dependencies).

For more details about dependencies and how to modify them, see the [How to deal with dependencies](dependencies-leapp-repository).

## Use convenience exceptions to stop the actor's execution

If you encounter unexpected input or any other error during execution of an actor and want to stop it, use these exceptions:

- [StopActorExecution](leapp.exceptions.StopActorExecution) - raising this exception is a convenient to stop actor's execution with no side effect - it has the same effect as returning `None` from the main `process()` method in the `actor.py`
- [StopActorExecutionError](leapp.exceptions.StopActorExecutionError) - raising this exception will stop actor's execution and notify the framework that an error has occurred and can influence the result of the workflow execution.

In case of [StopActorExecutionError](leapp.exceptions.StopActorExecutionError) the execution of the workflow will stop or not according to the [policy](leapp.workflows.policies) defined in the workflow, there are three possibilities:

- [FailImmediately](leapp.workflows.policies.Policies.Errors.FailImmediately) - end the workflow execution right away
- [FailPhase](leapp.workflows.policies.Policies.Errors.FailPhase) - end the workflow execution after finishing the current phase
- [ReportOnly](leapp.workflows.policies.Policies.Errors.ReportOnly) - do not end the workflow execution at all and continue with logging the issue only

You can also use the [StopActorExecution](leapp.exceptions.StopActorExecution) and [StopActorExecutionError](leapp.exceptions.StopActorExecutionError) exceptions inside a private or shared library.

## Use the LEAPP and LEAPP\_DEVEL prefixes for new envars

In case you need to change a behaviour of actor(s) for testing or development purposes - e.g. be able to skip a functionality in your actor - use environment variables. Such environment variables should start with prefix *LEAPP\_DEVEL*. Such variables are not possible to use on production systems without special *LEAPP\_UNSUPPORTED* variable. This prevents users to break their systems by a mistake.

If you want to enable user to modify behaviour on production systems as well (e.g. enable user increase size of something the actor is producing), use just *LEAPP* prefix and ensure you inform user about the variable if needed.

In both cases, such environment variables should be mentioned in related commit messages.
