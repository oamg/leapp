# How to properly inhibit the RHEL 7 to 8 upgrade process

## Process Inhibition

With latest changes on Leapp and with new actors added to the el7toel8 Leapp
repository, any actor can inhibit the upgrade process by producing a specific
message when a problem is found. The message model to use in this case is
[Report](pydoc/leapp.reporting.html#leapp.reporting.Report).
If there is at least one Report message with the `'inhibitor'` group produced before
the Report phase, the upgrade will be stopped in the Reports phase, in which the
messages are being collected. It means that any Report message produced
**after** the Report phase will **not** have inhibiting effect. The details
mentioned in the Report messages will be part of the report available to the
user to review.

### Sample Actor

Let’s start with a very simple actor that will verify if system architecture is
supported (this actor may be removed in the future as more archs will be supported):

```python
import platform

from leapp.actors import Actor
from leapp.tags import ChecksPhaseTag


class CheckSystemArch(Actor):
   """
    Check if system is running at a supported architecture. If no, inhibit the upgrade process.

    Base on collected system facts, verify if current architecture is supported, otherwise produces
    a message to inhibit upgrade process
    """

    name = 'check_system_arch'
    consumes = ()
    produces = ()
    tags = (ChecksPhaseTag,)

    def process(self):
        if platform.machine() != 'x86_64':
            self.log.info("Unsupported arch!")
```

If this actor is executed using `snactor` tool in a system with unsupported
architecture, we will see the following output on log:

```sh
$ snactor run CheckSystemArch --verbose
2019-04-16 15:08:59.622 INFO     PID: 1996 leapp: Logging has been initialized
2019-04-16 15:08:59.638 INFO     PID: 1996 leapp.repository.sandbox: A new repository 'sandbox' is initialized at /home/leapp/sandbox
2019-04-16 15:08:59.695 INFO     PID: 2021 leapp.actors.check_system_arch: Unsupported arch!
```

If, instead of only adding a message to the log, the actor writer wants to make
sure that the upgrade process will be stopped in case of unsupported arch, the
actor needs to produce a [Report](/pydoc/leapp.reporting.html#leapp.reporting.Report)
message using one of the `report_*` functions from the [reporting](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/el7toel8/libraries/reporting.py)
shared library with the `'inhibitor'` group.

```python
import platform

from leapp.actors import Actor
from leapp.reporting import Report, create_report
from leapp import reporting
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class CheckSystemArch(Actor):
    """
    Check if system is running at a supported architecture. If no, inhibit the upgrade process.

    Base on collected system facts, verify if current architecture is supported, otherwise produces
    a message to inhibit upgrade process
    """

    name = 'check_system_arch'
    consumes = ()
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        if platform.machine() != 'x86_64':
            create_report([
                reporting.Title('Unsupported architecture'),
                reporting.Summary('Upgrade process is only supported on x86_64 systems.'),
                reporting.Severity(reporting.Severity.HIGH),
                reporting.Groups([reporting.Groups.INHIBITOR, reporting.Groups.SANITY]),
            ])
```

Running the actor again, it is possible to verify that a new message was
generated. We will still use `snactor` tool to run the actor, but passing
`--print-output` this time to output all generated messages by the actor:

```sh
$ snactor run CheckSystemArch --verbose --print-output
2019-04-16 15:20:32.74  INFO     PID: 2621 leapp: Logging has been initialized
2019-04-16 15:20:32.94  INFO     PID: 2621 leapp.repository.sandbox: A new repository 'sandbox' is initialized at /home/leapp/sandbox
[
  {
    "stamp": "2019-09-05T12:58:56.342095Z",
    "hostname": "leapp-20190904152934",
    "actor": "check_system_arch",
    "topic": "report_topic",
    "context": "9a064a30-5d16-44ba-a807-b7f08b3c4215",
    "phase": "NON-WORKFLOW-EXECUTION",
    "message": {
      "hash": "dc95adcfca56eae62b7fcceeb0477a6d8257c3dddd1b05b879ebdcf05f59d504",
      "data": "{\"report\": \"{\\\"audience\\\": \\\"sysadmin\\\", \\\"groups\\\": [\\\"inhibitor\\\", \\\"sanity\\\"], \\\"severity\\\": \\\"high\\\", \\\"summary\\\": \\\"Upgrade process is only supported on x86_64 systems.\\\", \\\"title\\\": \\\"Unsupported architecture\\\"}\"}"
    },
    "type": "Report"
  }
]

```

Or to inspect closely the message.data field, we could use `jq` tool:

```sh
snactor run CheckSystemArch --verbose --print-output | jq '.[] | .message.data | fromjson'
{
  "report": "{\"audience\": \"sysadmin\", \"groups\": [\"inhibitor\", \"sanity\"], \"severity\": \"high\", \"summary\": \"Upgrade process is only supported on x86_64 systems.\", \"title\": \"Unsupported architecture\"}"
}

```

This is all that an actor needs to do in order to verify if some condition is
present on the system and inhibit the upgrade process based on that check.

After all the system checks are executed by different actors, an existing actor
named [VerifyCheckResults](https://github.com/oamg/leapp-repository/tree/master/repos/system_upgrade/el7toel8/actors/verifycheckresults)
is scheduled to run in the Leapp upgrade workflow. If some [Report](/pydoc/leapp.reporting.html#leapp.reporting.Report)
message with the `'inhibitor'` group was generated by some previous execution of
another actor in any previous phase of the workflow, like the sample one we just
wrote, the following output will be displayed to the user:

```sh
$ leapp upgrade
(...)
2019-04-16 15:36:54.696 INFO     PID: 7455 leapp.workflow: Starting phase Reports
2019-04-16 15:36:54.715 INFO     PID: 7455 leapp.workflow.Reports: Starting stage Before of phase Reports
2019-04-16 15:36:54.764 INFO     PID: 7455 leapp.workflow.Reports: Starting stage Main of phase Reports
2019-04-16 15:36:54.788 INFO     PID: 7455 leapp.workflow.Reports: Executing actor verify_check_results
2019-04-16 15:36:54.923 INFO     PID: 7455 leapp.workflow.Reports: Starting stage After of phase Reports
2019-04-16 15:36:54.970 INFO     PID: 7455 leapp.workflow: Workflow interrupted due to the FailPhase error policy

============================================================
                        ERRORS
============================================================

2019-04-16 15:36:54.871634 [ERROR] Actor: verify_check_results Message: Unsupported arch
2019-04-16 15:36:54.888818 [ERROR] Actor: verify_check_results Message: Ending process due to errors found during checks, see /var/log/leapp-report.txt for detailed report.

============================================================
                     END OF ERRORS
============================================================
```
