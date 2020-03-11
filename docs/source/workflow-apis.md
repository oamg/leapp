# Workflow APIs

## Using Workflow APIs

To start using a Workflow API you have to know which API you are going to be using.
In this case we are assuming that the repository defines a v2 namespace with an API definition of MyExampleAPI.

Now to use it, you have to import the API class object you want to use and specify the type of the class in the `apis`
field.
This is necessary so all the messages that are consumed and produced by the API can be picked up by the framework
and the actor can depend on them.

Here is an example of the usage:

```python
from leapp.actors import Actor
from leapp.workflows.api.v2 import MyExampleAPI

class MyWorkflowAPIUsingActor(Actor):
    """ An example actor consuming the v2.MyExampleAPI Workflow API """
    produces = ()
    consumes = ()
    apis = (MyExampleAPI,)

    def process(self):
        api = MyExampleAPI()
        api.second(value=10)
```

## General workings of the Workflow API feature

In the leapp repository, you want to create the API in, create a directory called `apis`.
Now within the `apis` directory anything that is in there can be imported with the `leapp.workflows.api` prefix.
An example: 

You created a module `$repository/apis/example.py` this module can now be imported like this:

```python
from leapp.workflows.api import example
```

## Defining Workflow APIs

A basic Workflow API is defined like this:

```python
from leapp.workflows.api import WorkflowAPI

class MyExampleAPI(WorkflowAPI):
    pass
```

This of course is no good as this wouldn't do anything just yet. APIs are nothing else than python classes and one
just adds a method to it to make it available.

Here is a simple function added to the API:

```python
from leapp.workflows.api import WorkflowAPI

class MyExampleAPI(WorkflowAPI):
    def first(self):
        return 'First API function result'
```

### Working with messages

Now if your API is going to consume or produce any messages, those messages have to be declared the same way as they
are declared for Actors. Any Actor that specifies to use this API, will automatically inherit all the messages consumed
or produced by the API.

Let's assume we have defined two models: `Consumed` and `Produced` where the definitions look like this:
```python
from leapp.models import fields, Model
from leapp.topics import ExampleTopic

class Consumed(Model):
    topic = ExampleTopic


class Produced(Model):
    topic = ExampleTopic
    consumed = fields.Model(Consumed)
    value = fields.Integer()
```

We are now going to define a method `second` which expects one parameter called value. That function 
will produce a message of type `Produced` for each message of type `Consumed`. 

```python
from leapp.libraries.stdlib import api
from leapp.messages import Consumed, Produced
from leapp.workflows.api import WorkflowAPI

class MyExampleAPI(WorkflowAPI):
    consumes = (Consumed,)
    produces = (Produced,)

    def first(self):
        return 'First API function result'

    def second(self, value):
        # Creates a new message `Produced` for each message of type `Consumed` with the additional value passed by 
        # the caller.
        for consumed in api.consume(Consumed):
            self.produce(Produced(consumed=consumed, value=value))
```

### Tests

Workflow APIs support having tests defined for them. We actually encourage you to define them for your APIs.

Tests for APIs are supposed to be defines in the `apis/tests` directory.

### Depedencies

Workflow APIs can depend on another Workflow API, to allow API compositiion. Actors using APIs with dependencies on 
other APIs just have to specify the API they want to use and do not need to know that those depend on other APIs.

All consumes/produces are recursively summarized and joined with the Actors direct message dependencies.
The dependency of a Workflow API on another Workflow API is expressed the same way as it is expressed for actors,
using the `apis` field.

## API definition best practises

### Be always explicit about what messages the API consumes or produces

Even though a dependent API might consume or produce the message already, a modification of the dependent API might
cause failures. Also from a readability point of view it is much clearer what kind of messages the API works on.

### Keep API interfaces small and on the same topic

Do not try to make one API for all the things, you might quickly end up in a scenario where you will cause an actor
being unable to produce a message that your API already consumes, which causes a dependency resolution failure in the
framework.

### Use lazy evaluation and caching for messages consumed to improve efficiency

Some messages need to be used multiple times during multiple API calls. Imagine an API interface like this:

```python
class InstalledPackagesAPI(WorkflowAPI):
    consumes = (InstalledRPM,)

    def has_package(self, name): pass
```

Now an implementation of `has_package` could look like this:
```python
def has_package(self, name):
    lookup = {rpm.name for rpm in leapp.stdlib.api.consume(InstalledRPM)}
    return name in lookup
```

Which is fine, if this is called only once per actor. However in case it needs to be run multiple times consider this:

```python
class InstalledPackagesAPI(WorkflowAPI):
    consumes = (InstalledRPM,)

    def __init__(self):
        self._rpm_lookup = None

    @property
    def rpm_lookup(self):
        if not self._rpm_lookup:
            self._rpm_lookup = {rpm.name for rpm in leapp.stdlib.api.consume(InstalledRPM)}
        return self._rpm_lookup

    def has_package(self, name):
        return name in self.rpm_lookup
```

This way the API caches the package names and lazy loads them when needed for as long as the instance of this object
lives.

### Write tests that verify API contract compliance

We highly encouraged you to write tests for the API that ensure the contract of the API is fulfilled.
That means that data types have guaranteed fields and data are, as they are documented.

This will allow you API breaking changes to be detected instantly once you try to commit changes that would break it,
and enforce the API to be updated to be compliant. Not meaning that the tests should be fixed, but the code to be
changed in a way it will stay compatible.

As an example if you rename a field in a Model that previously has been returned as a data type, instead you create
a new data type or update the instance and make it be compatible with the previous version of the model.

```python
# Before
class RPM(Model):
    package_name = fields.String()
    version = fields.String()

# After
class RPM(Model):
    name = fields.String()
    version = fields.List(fields.Integer)
    version_string = fields.String()

# Possible mitigation
class RPMAPIWrapper(object):
    def __init__(self, rpm):
        self._rpm = rpm

    @property
    def package_name(self):
        return self._rpm.name

    @property
    def version(self):
        return self._rpm.version_string
```

And on the fly when returning the data you wrap all new Models of RPM in that APIWrapper.
This is only an example, of course. You can also just create a normal object.

The gist of this is to ensure API stability and that any one using the API is not caught by surprise and their
code gets broken.
