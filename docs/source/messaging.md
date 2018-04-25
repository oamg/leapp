## Using messaging to send data between actors

The Leapp framework uses messages to send data to other actors that are executed afterward.
Messages are defined through the models declared [earlier](first-actor.html#creating-a-model). Actors can consume these messages and produce data based on their input.

As an example, the actors consume Hostname messages, resolve IPs for those
hostnames, and create the ResolvedHostname model to send a new type of message.

### Creating the ResolvedHostname model

Create the ResolvedHostname model by using the snactor tool.

```shell
$ snactor new-model ResolvedHostname
```

Assign the SystemInfoTopic to the new model and add two fields:
* The `name` field represents the hostname.
* The `ips` field contains a list of strings with IPv4 or IPv6 addresses.

Both fields are required in this scenario.

```python
from leapp.models import Model, fields
from leapp.topics import SystemInfoTopic


class ResolvedHostname(Model):
    topic = SystemInfoTopic
    name = fields.String(required=True)
    ips = fields.List(fields.String(), required=True)
```

### Creating a message consuming actor

Create a new actor that resolves the IPs for the hostnames:

```shell
$ snactor new-actor IpResolver
```

Import the ScanTag from leapp.tags, and the models Hostname and
ResolvedHostname from leapp.models. To retrieve the Hostname
messages to process their data, set it in the consumes tuple.
The result will be ResolvedHostname, so set the type in the
produces tuple.

The tags tuple gets extended with the ScanTag.
Now, import the socket library.

To enable actors to consume messages, use the consume method, and pass the type
of the message to be consumed. This is necessary to filter out the
messages. In theory, all messages can be consumed, but it is not recommended.
If you would like to change your code later and consume more
types of messages, you might end up with unexpected results. Always
specify the consume method for all types of messages to be consumed instead
of retrieving all messages unfiltered.

Now, perform the resolving of the hostnames, and produce a new message.

See the example of the code:

```python
import socket

from leapp.actors import Actor
from leapp.tags import ScanTag
from leapp.models import Hostname, ResolvedHostname


class IpResolver(Actor):
    name = 'ip_resolver'
    description = 'No description is provided for the ip_resolver actor.'
    consumes = (Hostname,)
    produces = (ResolvedHostname,)
    tags = (ScanTag,)

    def process(self):
        self.log.info("Starting to resolve hostnames")
        for hostname in self.consume(Hostname):
            resolved = socket.getaddrinfo(
                    hostname.name, None, 0, socket.SOCK_STREAM,
                    socket.IPPROTO_TCP)
            # Filtering out link local IPv6 addresses which contain a %
            ips = [entry[4][0] for entry in resolved if not '%' in entry[4][0]]
            self.produce(ResolvedHostname(name=hostname.name, ips=ips))
```

### Storing messages in the project data for reuse

The `snactor` framework tool saves the output of actors as locally stored messages,
so that they can be consumed by other actors that are being developed.

To make the data consumable, run the actor producing the data with the --save-output option:

```shell
$ snactor run --save-output HostnameScanner
```

The output of the actor is stored in the local project data file, and it can be used
by other actors.

### Testing the new actor

With the input messages available and stored, the actor can be tested.

```shell
$ snactor run --print-output IpResolver
2018-04-03 09:01:40.114 INFO     PID: 28841 leapp: Logging has been initialized
2018-04-03 09:01:40.115 INFO     PID: 28841 leapp.repository.tutorial: New repository 'tutorial' initialized at /home/evilissimo/devel/tutorial
2018-04-03 09:01:40.166 INFO     PID: 28860 leapp.actors.ip_resolver: Starting to resolve hostnames
[
  {
    "stamp": "2018-04-03T09:01:40.225635Z",
    "hostname": "actor-developer",
    "actor": "ip_resolver",
    "topic": "system_info",
    "context": "TESTING-CONTEXT",
    "phase": "NON-WORKFLOW-EXECUTION",
    "message": {
      "hash": "5fa31cac2237248f7c40df6a0190cc6acdd8a06c53c593aac2d93b8b3db58a70",
      "data": "{\"ips\": [\"fd15:4ba5:5a2b:1003:b14d:ed7:6c03:76cd\", \"192.168.89.153\"], \"name\": \"actor-developer\"}"
    },
    "type": "ResolvedHostname"
  }
]
```

#### Screencast

<asciinema-player src="_static/screencasts/messaging.json"></ascinema-player>
