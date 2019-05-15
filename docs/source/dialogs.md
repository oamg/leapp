# Asking user questions

Leapp framework uses dialogs to ask user for any additional information an actor may need.
Dialogs contain Components which represent individual questions.
Complete list of component types can be found in [documentation](pydoc/leapp.dialogs.html#module-leapp.dialogs.components).

As an example we will change [IpResolver](messaging.html#creating-a-message-consuming-actor) actor in a way that user will decide which hostnames will be resolved.


### Creating the dialog

Import Dialog and MultipleChoiceComponent from leapp.dialog and leapp.dialog.components respectively.
Create an instance of Dialog, specifying scope which is used to identify data in answer files, 
reason to explain user what the data will be used for and components. For each component specify key which will be used to get answer to specific question,
label and description. You can also specify default or choices if the component support them,
but as choices in our example depend on consumed data, we will specify them later.

See the example of the code:

```python
from leapp.dialogs import Dialog
from leapp.dialogs.components import MultipleChoiceComponent

class IpResolver(Actor):
    """
    No description has been provided for the ip_resolver actor.
    """
    name = 'ip_resolver'
    consumes = (Hostname,)
    produces = (ResolvedHostname,)
    tags = (ScanTag,)
    dialogs = (Dialog(scope='ipresolver', reason='Confirmation', components=(
        MultipleChoiceComponent(key='hostname', label='Please select hostnames to resolve',
                                description='No description'),)),)
```

### Using the dialog and the answers

In the function process we will first get the component of the dialog its key,
then set the choices from consumed data and default.
To ask the question, use request_answers method and pass the dialog which needs to be answered.
Then, we can get the hostnames selected by user from answers by component key and resolve them.

See the example of the code:

```python
def process(self):
    self.log.info("Starting to resolve hostnames")
    component = self.dialogs[0].component_by_key('hostname')
    component.choices = [hostname.name for hostname in self.consume(Hostname)]
    component.default = component.choices
    answer = self.request_answers(self.dialogs[0])
    for hostname in answer.get('hostname'):
        resolved = socket.getaddrinfo(
                hostname, None, 0, socket.SOCK_STREAM,
                socket.IPPROTO_TCP)
        # Filtering out link local IPv6 addresses which contain a %
        ips = [entry[4][0] for entry in resolved if not '%' in entry[4][0]]
        self.produce(ResolvedHostname(name=hostname, ips=ips))
```
