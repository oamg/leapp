# Writing tests for actors

The Leapp framework provides support for easily writing unit and component
tests for actors and also allows easy execution of the whole actors within
those tests. See [this document](test-actors.html)
to find out what is the difference between unit and component tests.

## Getting started with writing tests

Tests are considered being part of the actor and we do not only encourage but
basically require you to write tests if you want the actors to be accepted into
the git repository. To read more about what we ask from you when submitting
your work for our review, see
[Contributing guidelines for writing actors](https://github.com/oamg/leapp-repository/blob/master/CONTRIBUTING.md).

Tests for an actor are to be placed within the actor's directory, in a
subdirectory called `tests`. The layout for an actor `MyActor` in the
repository could look like this:

```
actors\
    myactor\
        actor.py
        tests\
            component_test.py
            unit_test.py
```

### Naming conventions

To have the tests found and carried out by [pytest framework](https://pytest.org),
all test functions have to:
 - reside in `test_*.py` or `*_test.py` files,
 - be prefixed by `test_`.

See the [pytest documentation](https://docs.pytest.org/en/latest/goodpractices.html#tests-outside-application-code).

### Writing tests that execute the whole actor - component tests

Now let's assume you want to write a test that executes the actor. This is how
your `component_test.py` from above could look like:

```python
def test_actor_execution(current_actor_context):
    current_actor_context.run()
```

This example makes use of the [current_actor_context](pydoc/leapp.html#leapp.snactor.fixture.current_actor_context)
fixture and will execute the `MyActor` actor.

Now if you would want to check that it produced an imaginary model called
`ProducedExampleModel` you can check this with the help of the `consume`
method.

```python
from leapp.models import ProducedExampleModel

def test_actor_execution(current_actor_context):
    current_actor_context.run()
    assert current_actor_context.consume(ProducedExampleModel)
```

If your actor requires input data that it can consume, you can specify the
input data with the help of the `feed` method of the `current_actor_context`
fixture.

```python
from leapp.models import ConsumedExampleModel, ProducedExampleModel

def test_actor_execution(current_actor_context):
    current_actor_context.feed(
        ConsumedExampleModel(value=1),
        ConsumedExampleModel(value=2))
    current_actor_context.run()
    assert current_actor_context.consume(ProducedExampleModel)
    assert current_actor_context.consume(ProducedExampleModel)[0].value == 3
```

#### Fixtures

The unit testing support was first implemented with the help of
[pytest fixtures](https://docs.pytest.org/en/latest/fixture.html).
Nowadays, we encourage you to use only the `current_actor_context` fixture
mentioned above. However the other fixtures have been preserved and are
still possible to use - see their [documentation](pydoc/leapp.html#module-leapp.snactor.fixture).

#### Testing actors that modify the OS

If your actor is checking the state of the system or modifying it in any way,
you have two choices to test such functionality:
- in the test, before executing the actor using the
`current_actor_context.run()`, change the system on which the tests are executed
as necessary and after executing the actor, revert back all the changes, so that
other tests work with the same environment. This option may be quite challenging
and in some cases not doable, for example when disabling SELinux which requires
reboot.
- replace the functions that read or modify the system with functions that do
not alter the system and return what you specify in the test. This is called
mocking. Currently it is not possible to mock any function while using the
`current_actor_context.run()`. But, mocking is possible in an actor's library.
For that, read further.

### Testing private actor library - unit tests

Leapp allows actors to relocate their code into actor private library. This
allows for better testability since the current implementation of Leapp does
not allow tests to import anything from the `actor.py`. Thus the code that is
supposed to be unit tested is necessary to move into the actor's private
library. Modules from the private library can then be imported not only from
the `actor.py` but also from the test modules.

Let's assume your actor has a private library module called `private.py`.

```
actors\
    myactor\
        actor.py
        libraries\
            private.py
        tests\
            unit_test.py
```

And the `private.py` looks like this:

```python
def my_function(value):
    return value + 42
```

You can easily write a test for this library like this:

```python
    from leapp.libraries.actor import private

    def test_my_actor_library():
        assert private.my_function(0) == 42
        assert private.my_function(1) == 43
        assert private.my_function(-42) == 0
```

### Using repository resources during test runtime

It is possible to test other things in the repository your actor is in and in
the [linked repositories](repo-linking.html). For example you may want to test
shared libraries, models, etc.

```python
    from leapp.libraries.common import useful_library
    from leapp.models import ExampleModel, ProcessedExampleModel

    def my_repository_library_test():
        e = ExampleModel(value='Some string')
        result = shared.process_function(e)
        assert type(result) is ProcessedExampleModel
```

## Running the tests

### Actor's tests

Use _pytest_ to run the tests for your actor. For the test modules to be able to
import leapp modules, you need to set `LEAPP_TESTED_ACTOR` environment variable
to the path of the actor under test.

Example of running `MyActor` actor tests:

```
$ pwd
/usr/share/leapp-repository/repositories/system_upgrade/el7toel8
$ LEAPP_TESTED_ACTOR="$PWD/actors/myactor" pytest -sv actors/myactor
```

To run one specific test, do it this way:
```
$ LEAPP_TESTED_ACTOR="$PWD/actors/myactor" pytest -sv \
  actors/myactor/tests/unit_test.py::test_one_of_my_library_functions
```

The _-s_ option of _pytest_ allows you to see standard output of the test code.
That is useful when you are debugging using printing to standard output.

To execute unit tests of all actors from all Leapp repositories in the
`leapp-repository` GitHub repository, first install test dependencies for each
actor by running  `make install-deps` and then issue `make test` in the root
directory of the `leapp-repository`.
Though running all tests this way is useful mostly for CI.

### Actors's test dependencies

If your **actor's tests** require a special package for their execution, create a
Makefile in the [actor's root directory](repository-dir-layout.html) with an
`install-deps` target calling `yum install -y`.

```
$ cat actors/myactor/Makefile
install-deps:
	yum install -y my-tests-need-this-pkg
```

Note: Dependencies defined the way mentioned above is for test execution only.
If your actor requires any package when executed as part of a workflow, it
needs to be specified in a
[leapp-repository specfile](https://github.com/oamg/leapp-repository/blob/master/packaging/leapp-repository.spec).

### Shared libraries' tests

To run tests of shared libraries (i.e. libraries stored in
`repositories/system_upgrade/el7toel8/libraries`) environment variable
`LEAPP_TESTED_LIBRARY` with path of the shared library needs to be specified for
_pytest_ to be able to import leapp modules.


To run tests for all shared libraries:
```sh
LEAPP_TESTED_LIBRARY="$PWD/libraries" pytest -sv libraries/tests
```

To run tests for one specific module:
```sh
LEAPP_TESTED_LIBRARY="$PWD/libraries" pytest -sv libraries/tests/test_my_library.py
```

To run one specific test of module:
```sh
LEAPP_TESTED_LIBRARY="$PWD/libraries" pytest -sv libraries/tests/test_my_library.py::test_something
```

It's also possible to use Makefile from the `leapp-repository` GitHub repository
for running tests of shared libraries:

```sh
TEST_LIBS=y make test
```
