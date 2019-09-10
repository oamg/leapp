# How to create a Leapp actor for RHEL 7 to 8 upgrade

## Introduction

This document is intended for all people who want to contribute to the process of upgrading Red Hat Enterprise Linux (RHEL) 7 to RHEL 8 using Leapp tool. The upgrade is performed in place meaning that the RHEL 7 installation is replaced by RHEL 8 on the same storage.
After reading through this document, you will be able to transform your expertise in certain parts of RHEL into improvements of the RHEL 7 to 8 upgrade tooling.

## Setting up the development environment

Leapp actors are written in Python 2.7+/3.6+ (the resulting code has to be both py2 and py3 compatible), so your usual Python development setup can be used during the process of creating a new actor.

## Tools

The main tools you will use for the actor development are listed below.

### leapp

The leapp framework uses provides the libraries required to be imported by any actor and also a binary tool used to control the execution of actors within a workflow.  

### snactor

Separate tool provided by Leapp to help the process of creating and executing an actor.

You can see _snactor_ source code [here](https://github.com/oamg/leapp/tree/master/leapp/snactor).

## Creating an actor

Every actor needs to be inside a so-called “Leapp repository”, otherwise it won’t be visible to Leapp. A Leapp repository groups actors and many other things which will be discussed later, like models, workflows, tags and topics. You can find all Leapp repositories under /usr/share/leapp-repository/repositories. A Leapp repository can be recognized by containing .leapp folder:

```shell
$ find -L /etc/leapp/repos.d/ -name ".leapp" -type d | xargs dirname
/etc/leapp/repos.d/common
/etc/leapp/repos.d/system_upgrade/el7toel8
```

First, you need to register repositories with snactor:

```shell
$ snactor repo find --path /etc/leapp/repos.d/
Registering /etc/leapp/repos.d/system_upgrade/el7toel8
Registering /etc/leapp/repos.d/common
```

After registering the repositories, you can move inside any of these repositories and use snactor to create a boilerplate of a new actor:

```shell
# cd /etc/leapp/repos.d/system_upgrade/el7toel8
# snactor new-actor MyNewActor
New actor MyNewActor has been created at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/actors/mynewactor/actor.py
# cd /usr/share/leapp-repository/repositories/system_upgrade/el7toel8/actors/mynewactor/
# tree
.
├── actor.py
└── tests
```

The main file of the actor is the actor.py in which you’ll write code for logic of the actor.

For further information about how create an actor read this [document](first-actor.html)

## Including an actor in the RHEL 7 to 8 upgrade process

Until now, you have created boilerplate of a new actor and made it visible to Leapp. But, Leapp needs some more information about what to do with the actor. Specifically, in which **“workflow”** and in which **“phase”** the actor should be executed. A workflow is a sequence of phases. The only workflow available now is the one solving the upgrade of RHEL 7 to RHEL 8. Each phase is a set of actors that will be executed one after another before the next phase starts. To find out in which workflow and phase should the actor be executed, Leapp looks for **“tags”**. To be part of RHEL 7 to RHEL 8 upgrade workflow, an actor needs to be tagged with **IPUWorkflowTag**.

The phases of the IPUWorkflow (in order) are: **Facts Collection, Checks, Report, Download, Upgrade RamDisk Preparation, Upgrade RamDisk Start, Late Tests, Preparation, RPM Upgrade, Application Upgrade, Third Party Applications, Finalization** and **First Boot**. Each phase has a specific tag that marks an actor as being part of that phase. You can find descriptions of all the phases and their tags [here](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/el7toel8/workflows/inplace_upgrade.py) and workflow diagram [here](inplace-upgrade-workflow.html).

For example, if an actor is to be executed within the Checks phase, it needs to be tagged both with IPUWorkflowTag and ChecksPhaseTag. The result after updating the boilerplate would be:

```python
from leapp.actors import Actor
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag

class MyNewActor(Actor):
    """ No description has been provided for the my_new_actor actor. """

    name = 'my_new_actor'
    consumes = ()
    produces = ()
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
            pass
```

## Inter-actor communication

### Receiving data from other actors

All communication between actors in Leapp is carried out using **“messages”**. An actor can consume or produce messages. A message may contain any data, but the data needs to be in a specific format defined by a **“model”**. If an actor wants to consume a message produced by another actor, it needs to specify the specific model of the consumed messages. Leapp will make sure to execute such an actor only after some message of the specified model was produced by another actor. If no message of the specified model was produced in previous phases or in the current phase, the consuming actor will get no messages of that kind.

One of the existing models in Leapp is [ActiveKernelModulesFacts](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/el7toel8/models/activekernelmodulesfacts.py). Messages from this model contain data about the system on which Leapp has been started. For example, it contains installed kernel modules. If an actor wants to perform some action based on existing kernel modules on the system, the actor can get list of these modules by consuming the _ActiveKernelModulesFacts_ messages. By extending the boilerplate, the code could look like this:

```python
from leapp.actors import Actor
from leapp.models import ActiveKernelModulesFacts

from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class MyNewActor(Actor):
    """ No description has been provided for the my_new_actor actor. """

    name = 'my_new_actor'
    consumes = (ActiveKernelModulesFacts,)
    produces = ()
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                    self.log.info(active_module.filename)
```

By executing the above actor, all active kernel modules would be logged on output using log utilities inherited from the Actor class.

### Producing data for other actors and reporting

An actor can produce some data interesting enough for other actors to consume. It could be some parsed data, or content that will be displayed to the user in a report or even shared info between a subset of actors.

The process is very similar to the one used to consume messages, but now the new actor will produce them. Similar to ActiveKernelModulesFacts, Leapp has a Report model. Messages from this model contain data that will be displayed to the user during ReportsPhase. For example, an actor can warn the user in case a btrfs kernel module is active on the system. Then, the actor could looks like this:

```python
from leapp import reporting
from leapp.actors import Actor
from leapp.models import ActiveKernelModulesFacts
from leapp.reporting import Report, create_report
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag

class MyNewActor(Actor):
    """ No description has been provided for the my_new_actor actor. """

    name = 'my_new_actor'
    consumes = (ActiveKernelModulesFacts,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == 'btrfs':
                    create_report([
                        reporting.Title('Btrfs has been removed from RHEL8'),
                        reporting.Summary(
                            'The Btrfs file system was introduced as Technology Preview with the initial release'
                            ' of Red Hat Enterprise Linux 6 and Red Hat Enterprise Linux 7. As of versions 6.6'
                            ' and 7.4 this technology has been deprecated and removed in RHEL8.'),
                        reporting.ExternalLink(
                            title='Considerations in adopting RHEL 8 - btrfs has been removed.',
                            url='https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/'
                                'considerations_in_adopting_rhel_8file-systems-and-storage_considerations-in-'
                                'adopting-rhel-8#btrfs-has-been-removed_file-systems-and-storage'
                        ),
                        reporting.Severity(reporting.Severity.HIGH),
                        reporting.Flags([reporting.Flags.INHIBITOR]),
                        reporting.Tags([reporting.Tags.FILESYSTEM]),
                        reporting.RelatedResource('driver', 'btrfs')
                    ])
                    break

```

Final report is generated in **"txt"** and **"json"** format in `/var/log/leapp` directory at the end of either leapp preupgrade or leapp upgrade execution.

### Reporting tips

Apart from the above example you can also suggest a remediation.

**Remediations**

```
reporting.Remediation(commands=[['alternatives', '--set', 'python', '/usr/bin/python3']])
reporting.Remediation(hint='Please remove the dropped options from your scripts.')
reporting.Remediation(playbook=<link_to_playbook>)
```

In case of more report message tags then currently provided is needed, please open a GH issue or a PR.

**Available tags**

```
'accessibility', 'authentication', 'boot', 'communication', 'drivers', 'email', 'encryption',
'filesystem', 'firewall', 'high availability', 'kernel', 'monitoring', 'network', 'OS facts',
'python', 'repository', 'sanity', 'security', 'selinux', 'services', 'time management',
'tools', 'upgrade process'
```

**Flags**

Besides the above mentioned **"inhibitor"** flag, there is also a **"failure"** flag which is recommended to use when we report a command or other action failure.

**Related resources**

We recognize the following 6 types of resources:

```
reporting.RelatedResource('package', 'memcached')
reporting.RelatedResource('file', '/etc/passwd')
reporting.RelatedResource('service', 'postfix')
reporting.RelatedResource('directory', '/boot')
reporting.RelatedResource('repository', 'RHEL 7 Base')
reporting.RelatedResource('kernel-driver', 'vmxnet3')
reporting.RelatedResource('pam', 'pam_securetty')
```

The related resources are especially useful when you have a lot of accompanied objects like files or directories by your report and you would like to present it to the user in a specific way.

For further information about messaging read this [document](messaging.html)

## Testing your new actor

During development of your new actor, it is expected that you will test your work to verify that results match your expectations. You can do that by manually executing your actor, or writing tests on various levels (i.e unit tests, component tests, E2E tests).

### Executing a single actor

You should use snactor tool to run a single actor and verify its output. Assuming that there are no errors, the actor was placed inside a valid leapp repository and snactor tool is aware of such repository, you can call snactor run to execute it. Bellow we are executing the existing [OSReleaseCollector](https://github.com/oamg/leapp-repository/tree/master/repos/system_upgrade/el7toel8/actors/osreleasecollector) actor that provides information about operating system release from target system. For the `snactor run` command you can use either the actor’s folder name (osreleasecollector), the actor’s class name (OSReleaseCollector) or the value of the name attribute of the actor’s class (os_release_collector).

```shell
# pwd
/usr/share/leapp-repository/repositories/system_upgrade/el7toel8
# snactor run --verbose OSReleaseCollector
2018-11-23 11:16:25.126 INFO     PID: 4293 leapp: Logging has been initialized
2018-11-23 11:16:25.163 INFO     PID: 4293 leapp.repository.system_upgrade_el7toel8: A new repository 'system_upgrade_el7toel8' is initialized at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8
2018-11-23 11:16:25.212 INFO     PID: 4293 leapp.repository.common: A new repository 'common' is initialized at /usr/share/leapp-repository/repositories/common
```

As you can see the actor is executed without errors. But, by default, snactor does only display data logged by the actor. In order to display messages generated by the actor you can re-run the above command with _--print-output_ option.

```shell
# snactor run --verbose --print-output OSReleaseCollector
2018-11-23 11:32:42.193 INFO     PID: 4433 leapp: Logging has been initialized
2018-11-23 11:32:42.218 INFO     PID: 4433 leapp.repository.system_upgrade_el7toel8: A new repository 'system_upgrade_el7toel8' is initialized at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8
2018-11-23 11:32:42.265 INFO     PID: 4433 leapp.repository.common: A new repository 'common' is initialized at /usr/share/leapp-repository/repositories/common
[
  {
    "stamp": "2019-04-30T13:00:13.836063Z",
    "hostname": "leapp-20190429150826",
    "actor": "os_release_collector",
    "topic": "system_info",
    "context": "0ac49430-1b29-4940-92bb-3e81da85f8af",
    "phase": "NON-WORKFLOW-EXECUTION",
    "message": {
      "hash": "8305f6a38dcd266ea02bbd2e7c0b799e871d7dbe8734ea4138da53f4779b993e",
      "data": "{\"id\": \"rhel\", \"name\": \"Red Hat Enterprise Linux Server\", \"pretty_name\": \"Red Hat Enterprise Linux\", \"variant\": \"Server\", \"variant_id\": \"server\", \"version\": \"7.6 (Maipo)\", \"version_id\": \"7.5\"}"
    },
    "type": "OSReleaseFacts"
  }
]
```

Now we can see that the _OSReleaseCollector_ actor produced a message of the _OSReleaseFacts_ model, containing data like OS Release name and version.

### Executing the whole upgrade workflow with the new actor

Finally, you can make your actor part of the “leapp upgrade” process and check how it behaves when executed together with all the other actors in the workflow. Assuming that your new actor is tagged properly, being part of _IPUWorkflow_, and part of an existing phase, you can place it inside an existing leapp repository on a testing RHEL 7 system. All Leapp components (i.e actors, models, tags) placed inside **/etc/leapp/repos.d/system_upgrade/el7toel8/** will be used by the “leapp upgrade” command during upgrade process.

### Verifying correct communication between actors

Leapp provides another actor, named [CheckOSRelease](https://github.com/oamg/leapp-repository/tree/master/repos/system_upgrade/el7toel8/actors/checkosrelease), that consumes messages from model _OSReleaseFacts_ and produces an error message in case system OS Release is not supported by Leapp upgrade process. In order to consume such message, _OSReleaseCollector_ actor needs to be executed before _CheckOSRelease_ and its message needs to be stored inside Leapp database. This process is controlled by the framework during the execution of “leapp upgrade” command.

But, if you want to execute it manually, for test purposes, you can also use snactor for it. First we need to make sure that all messages that will be consumed are generated and stored. For this example, this means running _OSReleaseCollector_ actor with the _--save-output_ option of snactor:

```shell
# snactor run --verbose --save-output OSReleaseCollector
2018-11-23 13:06:30.706 INFO     PID: 17996 leapp: Logging has been initialized
2018-11-23 13:06:30.753 INFO     PID: 17996 leapp.repository.system_upgrade_el7toel8: A new repository 'system_upgrade_el7toel8' is initialized at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8
2018-11-23 13:06:30.803 INFO     PID: 17996 leapp.repository.common: A new repository 'common' is initialized at /usr/share/leapp-repository/repositories/common
```

Now, you can execute _CheckOSRelease_ actor and verify that it consumes the previously generated message and produces a message saying that the target system is not supported by Leapp upgrade process. You don’t need to specify which message will be consumed, snactor will take care of it.

```shell
# snactor run --verbose --print-output CheckOSRelease
2018-11-23 13:11:15.549 INFO     PID: 18126 leapp: Logging has been initialized
2018-11-23 13:11:15.578 INFO     PID: 18126 leapp.repository.system_upgrade_el7toel8: A new repository 'system_upgrade_el7toel8' is initialized at /usr/share/leapp-repository/repositories/system_upgrade/el7toel8
2018-11-23 13:11:15.617 INFO     PID: 18126 leapp.repository.common: A new repository 'common' is initialized at /usr/share/leapp-repository/repositories/common
[
  {
    "stamp": "2019-04-30T13:12:05.706317Z",
    "hostname": "leapp-20190429150826",
    "actor": "check_os_release",
    "topic": "report_topic",
    "context": "0ac49430-1b29-4940-92bb-3e81da85f8af",
    "phase": "NON-WORKFLOW-EXECUTION",
    "message": {
      "hash": "ceaf419907ec78a894334b2a331a9ebb0c5a7847c18afc6d7546ba6656959e0d",
      "data": "{\"report\": \"{\\\"audience\\\": \\\"sysadmin\\\", \\\"detail\\\": {\\\"related_resources\\\": [{\\\"scheme\\\": \\\"file\\\", \\\"title\\\": \\\"/etc/os-release\\\"}]}, \\\"flags\\\": [\\\"inhibitor\\\"], \\\"severity\\\": \\\"high\\\", \\\"summary\\\": \\\"The supported OS versions for the upgrade process: 7.6\\\", \\\"tags\\\": [\\\"sanity\\\"], \\\"title\\\": \\\"Unsupported OS version\\\"}\"}"
    },
    "type": "Report"
  }
]

```

To flush all saved messages from the repository database, run `snactor messages clear`.

## Writing tests for an actor

[Read the tutorial](unit-testing.html) for writing an running unit and component tests

## Best practices

Read the best practices [document](best-practices.html) and [Python guidelines](https://github.com/oamg/leapp-guidelines/blob/master/python-coding-guidelines.md)

## Contributing actors to the Leapp project

Currently all Leapp elements (i.e. actors, models, tags) are stored under a public [GitHub repository](https://github.com/oamg/leapp-repository)

All new content that needs to be part of Leapp release distributed to all users should be proposed as a Pull Request in this repository.

**Before submitting your work for review, make sure you have read and followed the contribution guidelines:**

[Contribution guidelines for writing actors](contributing.html)

This [pull request](https://github.com/oamg/leapp-repository/pull/186) gives a good example of both guidelines-driven actor implementation and thorough test coverage.

## FAQ

### In which existing workflow phase should I place my new actor?

You can decide that based on the description of the phases this information is available in the [code](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/el7toel8/workflows/inplace_upgrade.py) and diagram [here](inplace-upgrade-workflow.html). Please note that if your actor depends on some message generated by another actor, it cannot be executed in a phase before the phase of such actor. In a similar way, if your actor produces data, it needs to be executed before the actor consuming the data.

### How to stop the upgrade in case my actor finds a problem with the system setup?

The process of inhibiting the upgrade is done by the VerifyCheckResult actor, executed during the ReportPhase. This actor consumes messages from the _Report_ model and if any message with the flag “inhibitor” was generated it will inhibit the upgrade process. So, your actor needs to produce a _Report_ message with the flag “inhibitor” before the upgrade process gets to the ReportPhase. Read more about inhibiting the upgrade process [here](inhibit-rhel7-to-rhel8.html).

### How to stop execution of my actor in case of an unexpected error?

It’s good practice to code defensively so the code is robust. The actor should detect unexpected input or result of some operation and exit gracefully instead of tracebacking. In case you detect an unexpected behavior, let the framework know about it by raising [StopActorExecutionError](pydoc/leapp.html#leapp.exceptions.StopActorExecutionError). Framework will act based on the [setting of the upgrade workflow](pydoc/leapp.workflows.html?highlight=FailPhase#module-leapp.workflows.policies) in one of the following three ways:

- end the upgrade process right away, or
- end the upgrade process after finishing the current phase, or
- do not end the upgrade process at all and continue with logging the issue only.

### How does the logging work?

For logging of messages not to be visible to the user by default but rather for issue investigation purposes, use simply `self.log.<level>(msg)` within the actor. Or, within the actor’s library this way:

```python
from leapp.libraries.stdlib import api
api.current_logger().<level>(msg)
```

The usual logging practice of [Python’s logger library](https://docs.python.org/2/library/logging.html#logger-objects) applies, i.e. the `<level>` can be for example _debug, warning, error, critical_, etc. Leapp framework will take care of these messages and provide them through appropriate channels (stdout/stderr, log files, journalctl, audit table in /var/lib/leapp/leapp.db).

### What Python version my actor/tests code should be compatible with?

Python 2.7+/3.6+, but keep in mind that the resulting code has to be both py2 and py3 compatible.

### How to add tests to my new actor?

Under “tests” folder, an actor can have Python files containing tests that will be executed using PyTest. Leapp provide tests utilities to simulate actor consuming and checking actor production. Please, refer to detailed Leapp documentation about how to write tests.

For further information read: [Writing tests for actors](unit-testing.html)

### How to use libraries or data files in my new actor?

An actor can have data files under the “files” folder and Python libraries under the “libraries” folder. Leapp does provide utilities to help an actor to access the files and libraries in these folders. Please, refer to detailed Leapp documentation about this.

### Where can I report an issue or RFE related to the framework or other actors?

You can open a GitHub issues:

- [Leapp framework](https://github.com/oamg/leapp/issues/new)
- [Leapp actors](https://github.com/oamg/leapp-repository/issues/new)

When filing an issue, include:

- How to reproduce it
- All files in `/var/log/leapp`.
- The `/var/lib/leapp/leapp.db` file.

## Where can I seek help?

We’ll gladly answer your questions and lead you to through any troubles with the actor development. You can reach us, the OS and Application Modernization Group, at freenode IRC server in channel __#leapp__.
