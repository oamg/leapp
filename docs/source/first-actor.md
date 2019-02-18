# Creating your first actor

We will go through the steps necessary to create a new actor in a completely clean environment.
The purpose of the actor in this tutorial is to retrieve the hostname of the
system and to send it as a message into the system, so that other actors can consume it.

We will start at the very beginning, so we will assume that all things have to be created.

## Getting started

First, create and go to your repository directory. See [Creating a new repository tutorial](create-repository).

### Creating a tag

Create a tag. Since we are scanning the system, let's
call this tag 'Scan'. Use the snactor tool.

```shell
    $ snactor new-tag Scan
```

This will create a subdirectory called tags with a scan.py file. The file contains all
the necessary code, and it creates the *ScanTag* class, which we will use
later.

#### Screencast

<asciinema-player src="_static/screencasts/create-tag.json"></ascinema-player>

### Creating a topic

Create the *SystemInfo* topic.

```shell
    $ snactor new-topic SystemInfo
```

The topics directory has been created with a systeminfo.py file, which provides
the complete code and definition for the *SystemInfoTopic* class used in the model.

#### Screencast

<asciinema-player src="_static/screencasts/create-topic.json"></ascinema-player>

### Creating a model

Create a model for sending a message. We will call the
model *Hostname* and have it assigned to the *SystemInfoTopic* class.

```shell
   $ snactor new-model Hostname
```

The model boiler plate is available at the models/hostname.py file:

```python
from leapp.models import Model, fields


class Hostname(Model):
    topic = None #  TODO: import appropriate topic and set it here
```

As the comment says, import the *SystemInfoTopic* class and assign it to
the topic variable of the *Hostname* model.

Import the *SystemInfoTopic* class:
```python
from leapp.topics import SystemInfoTopic
```

After the topic has been assigned, create a new field for the message
called *name*, which is supposed to be a string. This can be accomplished by
setting the *name* field:

```python
class Hostname(Model):
    topic = SystemInfoTopic
    name = fields.String()
```

Add a default value of 'localhost.localdomain', in case the name
is not specified. Default values are initializing the values in the
construction of the class object, if no other value has been determined.

```python
class Hostname(Model):
    topic = SystemInfoTopic
    name = fields.String(default='localhost.localdomain')
```

Save the file and write an actor.

#### Screencast

<asciinema-player src="_static/screencasts/create-model.json"></ascinema-player>


### Creating an actor

We are creating an actor
that retrieves the system hostname and sends it as a message.
Call the actor *HostnameScanner*.

```shell
    $ snactor new-actor HostnameScanner
```

We created the actors/hostnamescanner/ directory with an actor.py file
and a tests subdirectory. Let's look at the pregenerated actor.py file:

```python
from leapp.actors import Actor


class HostnameScanner(Actor):
    name = 'hostname_scanner'
    description = 'No description has been provided for the hostname_scanner actor.'
    consumes = ()
    produces = ()
    tags = ()

    def process(self):
        pass
```

Import the model and the tag we have previously created to
be able to assign them.

```python
from leapp.models import Hostname
from leapp.tags import ScanTag
```

Assign *Hostname* to the *produces* attribute as a tuple element and
do the same with the *ScanTag* and *tags* attributes.
Do not forget the trailing commas.

```python
     consumes = ()
     produces = (Hostname,)
     tags = (ScanTag,)
```

Now, we can start writing the actor code. The actor code has to be added
in the process method.

To retrieve the hostname, we will use the python socket module, which has
a function called *getfqdn*, which will retrieve the hostname.

For that, add `import socket` at the top of the file.

A very minimal implementation for this actor can look like this:

```python
    def process(self):
        self.produce(Hostname(name=socket.getfqdn()))
```

But we would also like to do some logging, so that we can see our actor at work.

```python
   def process(self):
       self.log.info("Starting to scan for the hostname")
       hostname = socket.getfqdn()
       self.produce(Hostname(name=hostname))
       self.log.info("Finished scanning for the hostname, found = %s",
                     hostname)
```

You can edit the description of the actor now.

Save the file, and it is ready to be run from the commandline:

```shell
    $ snactor run --debug HostnameScanner
    2018-03-20 13:24:06.20  INFO     PID: 6256 leapp: Logging has been initialized
    2018-03-20 13:24:06.22  INFO     PID: 6256 leapp.repository.tutorial: New repository 'tutorial' initialized at /home/evilissimo/devel/tutorial
    2018-03-20 13:24:06.67  INFO     PID: 6273 leapp.actors.hostname_scanner: Starting to scan for the hostname
    2018-03-20 13:24:16.188 INFO     PID: 6273 leapp.actors.hostname_scanner: Finished scanning for the hostname, found = actor-developer
```

To see the message it generated, use the --print-output option:

```shell
    $ snactor run --debug --print-output HostnameScanner
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

