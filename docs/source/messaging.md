## Using messaging to send data between actors

The Leapp framework uses messages to send data to other actors are executed afterwards.
Messages are defined through the models we have declared [earlier](first-actor.html#creating-a-model). Actors can consume those messages and produce data based on their input.

As an example in this part of the tutorial, we will consume Hostname messages and resolve the IPs for those
hostnames and create a ResolvedHostname model to send a new type of message.

### Creating the new ResolvedHostname model

First we will create the new model ResolvedHostname using the snactor tool.

```shell
$ snactor new-model ResolvedHostname
```

Next we will assign the SystemInfoTopic to the new model and add two fields:
* The field `name` represents the hostname
* The fields `ips` will contain a list of strings with the IPv4 or IPv6 addresses

Both fields are required in this scenario.

```python
from leapp.models import Model, fields
from leapp.topics import SystemInfoTopic


class ResolvedHostname(Model):
    topic = SystemInfoTopic
    name = fields.String(required=True)
    ips = fields.List(fields.String(), required=True)
```

### Creating the message consuming actor

Now we will create the new actor that does resolve the IPs for the hostnames.

```shell
$ snactor new-actor IpResolver
```

We will import the ScanTag from leapp.tags and the models Hostname and
ResolvedHostname from leapp.models. Since we want to retrieve the Hostname
messages to process their data we set it in the consumes tuple.
And our result will be ResolvedHostname so we are setting the type in the
produces tuple.

The tags tuple gets extended with the ScanTag.
Next we will just import socket.

To consume messages we will use the class method consume and pass the type
of message we would like to consume. Actually this is just to filter out the
messages. In theory we could just consume all messages, but it's recommended
not to do so. If you would like to change your code later and consume more
types of messages you might end up with unexpected results. So rather always
specify on the 'consume' method all types you would like to consume instead
of getting all messages unfiltered.

Now we just perform the resolving of the hostnames and produce a new message.

See the example code here:

```python
import socket

from leapp.actors import Actor
from leapp.tags import ScanTag
from leapp.models import Hostname, ResolvedHostname


class IpResolver(Actor):
    name = 'ip_resolver'
    description = 'For the actor ip_resolver has been no description provided.'
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

The framework tool `snactor` allows to save the output of actors as locally stored messages,
so they can be consumed by actors that are being developed.

To make the data consumable to other actors, the actor producing the data has to be
run with the --save-output like this.

```shell
$ snactor run --save-output HostnameScanner
```

Now the output of the actor will be stored in the local project data file and can be used
by other actors.

### Testing the new actor

Now that we have the input messages available and stored the actor can be tested.

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
