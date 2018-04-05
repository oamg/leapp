# Creating a first actor

We will go through the steps necessary to create a new actor in a complete clean environment.
The purpose of the actor we will write in this tutorial, is to retrieve the hostname of the
system and send it as a message into the system so other actors can consume it.

For the sake of getting started from zero, we will assume that all things have to be created.

## Terminology

First let's start defining the terminology

### Models
To send messages between actors a model has to be created that describes the format of the
message and acts at the same time as an object to access the data. If you know ORM libraries,
this works pretty similar

### Topics
Topic are used to classify the purpose of a message and every Model has to have an assigned
topic.

### Tags
Tags are used by the framework to be able to query the repository for actors that should be
executed together in a [phase of a workflow](terminlogy.html#phase). This starts being
interesting when you want to have your actor being included into a
[workflow](terminology.html#workflow) in a phase. For keeping the tutorial a bit more simple
about how to write and test the actor we skip this topic.

### Actors
Actors define what messages they want to consume and what they produce by importing the
classes and assigning them to a tuple in the actor class definition.
Tags are defined there as well for the reasons as outlined above.


## Getting started

First go to your project directory. If you did not yet create a project please check the
steps [in the create project tutorial](create-project)

We're considering that this is an empty project.

### Creating a tag

As outlined above, we will have to create a tag. Since we are scanning the system, let's
call this tag 'Scan'

```shell
    $ snactor new-tag Scan
```

This will create a subdirectory called tags with a file scan.py and in that file all
necessary code is already defined and it creates the class *ScanTag* which we will use
later on.

#### Screencast

<asciinema-player src="_static/screencasts/create-tag.json"></ascinema-player>

### Creating a topic

Next we will have to create a topic, which we will call *SystemInfo* topic

```shell
    $ snactor new-topic SystemInfo
```

This time the folder topics has been created with a systeminfo.py file that provides
the complete code and definition for the *SystemInfoTopic* class we will use in the model.

#### Screencast

<asciinema-player src="_static/screencasts/create-topic.json"></ascinema-player>

### Creating a model

Now we have to create the model we want to use for sending the message. We will call the
model *Hostname* and have it assigned to the *SystemInfoTopic*

```shell
   $ snactor new-model Hostname
```

The model boiler plate will be now available at models/hostname.py and looks like this:

```python
from leapp.models import Model, fields


class Hostname(Model):
    topic = None #  TODO: import appropriate topic and set it here
```

As the comment says, we will have to import the SystemInfoTopic and assign it to
the topic variable of the Hostname class.

You can import the SystemInfoTopic class like this:
```python
from leapp.topics import SystemInfoTopic
```

After the topic has been assigned we will create a new field for the message
called name, which is supposed to be a string. This can be accomplished by
setting the name field like this:

```python
class Hostname(Model):
    topic = SystemInfoTopic
    name = fields.String()
```

Now let's add a default value of 'localhost.localdomain', in case the name
does not get set. Default values are initializing the values in the
construction of the class object, if there has not been passed any other
value.

```python
class Hostname(Model):
    topic = SystemInfoTopic
    name = fields.String(default='localhost.localdomain')
```

Now we can save the file a go write an actor using the other parts.

#### Screencast

<asciinema-player src="_static/screencasts/create-model.json"></ascinema-player>


### Creating an actor

So as we said in the introduction we said we would like to create an actor
that retrieves the system hostname and sends it as a message.
Therefore we will create an actor called HostnameScanner

```shell
    $ snactor new-actor HostnameScanner
```

We will receive a folder actors/hostnamescanner/ with an actor.py file
and a tests subfolder. Let's look at the pregenerated actor.py file:

```python
from leapp.actors import Actor


class HostnameScanner(Actor):
     name = 'hostname_scanner'
     description = 'For the actor hostname_scanner has been no description provided.'
     consumes = ()
     produces = ()
     tags = ()

     def process(self):
         pass
```

First we will have to import the model and the tag we have previously created to
be able to assign them.

```python
from leapp.models import Hostname
from leapp.tags import ScanTag
```

Now assign *Hostname*, to the *produces* attribute as a tuple element and
do the same with *ScanTag* and the *tags* attribute
Don't forget the trailing comma ;-)

```python
     consumes = ()
     produces = (Hostname,)
     tags = (ScanTag,)
```

Now we can start writing the actor code. The actor code has to be added
in the process method.

To retrieve the hostname, we will use the python socket module, which has
a function called getfqdn. This will retrieve us the hostname.

For that add `import socket` on the top of the file.

A very minimal implementation for this actor can look like this:

```python
    def process(self):
        self.produce(Hostname(name=socket.getfqdn()))
```

But we would like also to do some logging so we can see our actor at work.

```python
   def process(self):
       self.log.info("Starting to scan for the hostname")
       hostname = socket.getfqdn()
       self.produce(Hostname(name=hostname))
       self.log.info("Finished scanning for the hostname, found = %s",
                     hostname)
```

If you want, you can edit the description of the actor now.

Now we can save the file and it's ready to run from commandline via:

```shell
	$ snactor run HostnameScanner
    2018-03-20 13:24:06.20  INFO     PID: 6256 leapp: Logging has been initialized
    2018-03-20 13:24:06.22  INFO     PID: 6256 leapp.repository.tutorial: New repository 'tutorial' initialized at /home/evilissimo/devel/tutorial
    2018-03-20 13:24:06.67  INFO     PID: 6273 leapp.actors.hostname_scanner: Starting to scan for the hostname
    2018-03-20 13:24:16.188 INFO     PID: 6273 leapp.actors.hostname_scanner: Finished scanning for the hostname, found = actor-developer
```

If you want to see the message it generated use the --print-output flag

```shell
	$ snactor run --print-output HostnameScanner
	2018-03-20 13:24:32.333 INFO     PID: 6300 leapp: Logging has been initialized
	2018-03-20 13:24:32.335 INFO     PID: 6300 leapp.repository.tutorial: New repository 'tutorial' initialized at /home/evilissimo/devel/tutorial
	2018-03-20 13:24:32.372 INFO     PID: 6317 leapp.actors.hostname_scanner: Starting to scan for the hostname
	2018-03-20 13:24:42.492 INFO     PID: 6317 leapp.actors.hostname_scanner: Finished scanning for the hostname, found = actor-developer
	[
	  {
		"stamp": "2018-03-20T13:24:37.434408Z",
		"hostname": "actor-developer",
		"actor": "hostname_scanner",
		"context": "TESTING-CONTEXT",
		"phase": "NON-WORKFLOW-EXECUTION",
		"message": {
		  "hash": "fb5ce8e630a1b3171709c9273883b8eb499b6b2ba09e112832ad47fa4e3f62b7",
		  "data": "{\"name\": \"actor-developer\"}"
		},
		"type": "Hostname",
		"topic": "system_info"
	  }
	]
```

#### Screencast

<asciinema-player src="_static/screencasts/create-actor.json"></ascinema-player>

