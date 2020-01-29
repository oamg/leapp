# Asking user questions

Leapp framework uses dialogs to ask user for any additional information an actor needs that can not be deduced
automatically.
Dialogs contain Components which represent individual questions.
Complete list of component types can be found in
[documentation](pydoc/leapp.dialogs.html#module-leapp.dialogs.components).

As an example we will change [IpResolver](messaging.html#creating-a-message-consuming-actor) actor in a way that user
will decide which hostnames will be resolved.


### Creating the dialog

Import Dialog and MultipleChoiceComponent from leapp.dialog and leapp.dialog.components respectively.
Create an instance of Dialog, specifying scope which is used to identify data in the answer file,
reason to explain user what the data will be used for and components. For each component specify key which will be
used to get answer to specific question, label and description.
You can also specify default or choices if the component support them, but as choices in our example depend on
consumed data, we will specify them later.

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

To pose a question that needs to be answered use get_answers method and pass the dialog containing the question.

Be aware that from actor writers' perspective get_answers function is not blocking workflow execution - no
interactivity will be introduced by adding a get_answers call in actor's process() method; the value returned will
correspond to the option saved in answerfile if one is found or an empty dict is returned otherwise.

You don't need to specifically inhibit execution in case user doesn't provide an option - the leapp framework will
take care of that. A report entry with inhibitor type will be automatically created if the actor with a dialog is
executed during leapp preupgrade or leapp upgrade run and no prerecorded user choice has been registered in answerfile.
All interactivity that is necessary to record user options is part of leapp answer cli command; as an alternative
you can modify the generated answerfile manually with an editor of choice to contain the desired choices.

For example, to get the hostnames selected by user from answers by component key and resolve them:

```python
def process(self):
    self.log.info("Starting to resolve hostnames")
    component = self.dialogs[0].component_by_key('hostname')
    component.choices = [hostname.name for hostname in self.consume(Hostname)]
    component.default = component.choices
    answer = self.get_answers(self.dialogs[0])
    for hostname in answer.get('hostname'):
        resolved = socket.getaddrinfo(
                hostname, None, 0, socket.SOCK_STREAM,
                socket.IPPROTO_TCP)
        # Filtering out link local IPv6 addresses which contain a %
        ips = [entry[4][0] for entry in resolved if not '%' in entry[4][0]]
        self.produce(ResolvedHostname(name=hostname, ips=ips))
```

### Explaining the dialogs processing mechanism during the upgrade

The upgrade itself, from the operator's point of view, consists of 3 distinct stages: leapp preupgrade, leapp answer
and leapp upgrade.

Leapp preupgrade stage should be treated as "non-invasive system upgradeability analysis", when the upgrade workflow
stops right after preliminary system facts collection phases and a preupgrade report containing all the information
about potential issues is generated. If an actor containing dialog is discover during this stage, a specific
message is added to the preupgrade report file saying that for the successful upgrade the operator should record
their decision in the answerfile.

Leapp answer stage is intended specifically for answerfile management. The operator has the option to manually edit
the answerfile with editor of choice or use `leapp answer` command to fill the answerfile (usually located at 
/var/log/leapp/answerfile) with choices for the discovered dialogs. After modifying the answerfile you can check
system upgradeability by rerunning leapp preupgrade.

Leapp upgrade stage should be run only when leapp preupgrade successfully passes. In case any unanswered/bad choice
dialogs are encountered the upgrade process will stop and the report file will be generated telling the operator what
has gone wrong.
