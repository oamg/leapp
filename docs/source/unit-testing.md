# Unit testing actors

The Leapp framework provides support for easily writing unit tests for
actors and also allows easy execution of the whole actors within those
tests.

The support is implemented with help of
[pytest](https://docs.pytest.org/en/latest/)
[fixtures](https://docs.pytest.org/en/latest/fixture.html). The fixtures
provided by the Leapp framework reside in the `leapp.snactor.fixture`
module.

## Getting started with writing tests

Tests are considered being part of the actor and we do not only
encourage but basically require you to write tests if you want them to
be accepted into the git repository.

Tests for actors are located within the actors directory, in a sub
directory called `tests`

The layout for an actor `MyActor` in the repository could look like
this:

```
actors\
    myactor\
        actor.py
        tests\
            tests.py
```

### Writing tests that execute the whole actor

Now let's assume you would want to write a test that executes the actor.
This is how your `tests.py` from above could look like:
```python
from leapp.snactor.fixtures import current_actor_context

def test_actor_execution(current_actor_context):
    current_actor_context.run()
```

This example makes use of the
[current_actor_context](#current-actor-context) fixture and will
execute the `MyActor` actor.

Now if you would want to check that it produced an imaginary model
called `ProducedExampleModel` you can check this with the help of the
`consume` method:
```python
from leapp.snactor.fixtures import current_actor_context
from leapp.models import ProducedExampleModel

def test_actor_execution(current_actor_context):
    current_actor_context.run()
    assert current_actor_context.consume(ProducedExampleModel)
```

If your actor requires input data that it can consume, you can specify
the input data with the help of the `feed` method of the
`current_actor_context` fixture.

```python
from leapp.snactor.fixtures import current_actor_context
from leapp.models import ConsumedExampleModel, ProducedExampleModel

def test_actor_execution(current_actor_context):
    current_actor_context.feed(
        ConsumedExampleModel(value=1),
        ConsumedExampleModel(value=2))
    current_actor_context.run()
    assert current_actor_context.consume(ProducedExampleModel)
    assert current_actor_context.consume(ProducedExampleModel)[0].value == 3
```

And that is all about testing the execution of actors that is specific
to the framework. If your actor is modifying the file system, or
has other needs, you will have at this point to take care of it.

### Testing private actor libraries

Leapp allows actors to structure their code into actor private
libraries. This allows for better testability, since actor.py is
considered to be a black box. One can execute the whole actor, but
one cannot import anything from the actor.py of the actor.

If functionality needs to be tested, it's highly recommended to
move code that is supposed to be tested into libraries that are
imported from the actor and can also be imported into the testing
python modules.

Let's assume your actor has a private library called `private.py`

```
actors\
    myactor\
        actor.py
        libraries\
            private.py
        tests\
            tests.py
```

And your `private.py` looks like this:

```python
def my_function(value):
    return value + 42
```

You can easily write a test for this library like this:

```python
    from leapp.snactor.fixture import current_actor_libraries

    def test_my_actor_library(current_actor_libraries):
        from leapp.libraries.actor import private
        assert private.my_function(0) == 42
        assert private.my_function(1) == 43
        assert private.my_function(-42) == 0
```

**Note**: *The private libraries are only available within your test
function. You cannot import those functions on the global scope of the
test module.*

### Making Leapp repositories available on test runtime

It is possible to test other things in the repository your actor is in.
For example if you want to test shared libraries, models etc you can
use the `loaded_leapp_repository` fixture.


```python
    from leapp.snactor.fixture import loaded_leapp_repository
    from leapp.models import ExampleModel, ProcessedExampleModel

    def my_repository_library_test(loaded_leapp_repository):
        from leapp.libraries.common import shared
        e = ExampleModel(value='Some string')
        result = shared.process_function(e)
        assert type(result) is ProcessedExampleModel
```

Additionally `loaded_leapp_repository` gives you access to an instance
of [RepositoryManager](pydoc/leapp.repository.html#leapp.repository.manager.RepositoryManager).
For more information to the repository please check the documentation of
the RepositoryManager class.