# Reporting information to user
The previous tutorial described communication between `Actor`s. In this
tutorial the communication from `Actor`s to user is described.

This is done messages using a special
{ref}`Report<building-blocks-and-architecture:report>`. Reports can be produced
by actors similarly to standard messages.

Let’s start with a very simple actor that will verify if the system architecture is
supported:
```python
import platform

from leapp.actors import Actor
from leapp.tags import ScanTag


class CheckSystemArch(Actor):
   """
    Check if system is running on a supported architecture and inform the user if not.
    """

    name = 'check_system_arch'
    consumes = ()
    produces = ()
    tags = (ScanTag,)

    def process(self):
        if platform.machine() != 'x86_64':
            self.log.info("Unsupported architecture!")
```
currently, the actor only logs a message to the screen and to the logs file.
If this actor is executed using `snactor` tool in a system with unsupported
architecture, we will see the following output:
```sh
$ snactor run CheckSystemArch --verbose
2019-04-16 15:08:59.622 INFO     PID: 1996 leapp: Logging has been initialized
2019-04-16 15:08:59.638 INFO     PID: 1996 leapp.repository.sandbox: A new repository 'sandbox' is initialized at /home/leapp/sandbox
2019-04-16 15:08:59.695 INFO     PID: 2021 leapp.actors.check_system_arch: Unsupported arch!
```

However logs are not very good for structured information, reports enable
structured and human readable and customizable presentation of information to
the user.

Let's modify the `CheckSystemArch` actor to produce a report instead of the
log:
```python
import platform

from leapp.actors import Actor
from leapp.reporting import Report, create_report  # new imports
from leapp import reporting  # new imports
from leapp.tags import ScanTag


class CheckSystemArch(Actor):
    """
    Check if system is running on a supported architecture and inform the user if not.
    """

    name = 'check_system_arch'
    consumes = ()
    produces = (Report,)
    tags = (ScanTag,)

    def process(self):
        if platform.machine() != 'x86_64':
            create_report([
                reporting.Title('Unsupported architecture'),
                reporting.Summary('Upgrade process is only supported on x86_64 systems.'),
                reporting.Severity(reporting.Severity.HIGH),
                reporting.Groups([reporting.Groups.SANITY]),
            ])
```
The `create_report()` function takes a list of report fields and produces a
report. The report has a title, a summary describing the issue in more detail a
{py:class}`leapp.reporting.Severity`, and {py:class}`leapp.reporting.Groups`.
`Severity` and `Groups` can be used to classify reports. There are also other
fields, see {py:mod}`leapp.reporting` for more information.

The framework does not print or write the reports to a file by itself. Instead,
they can be retrieved via {py:func}`leapp.utils.audit.get_messages()` and the
presentation is left on the caller. Fox example, Leapp is used for Red Hat Enterprise Linux
in-place upgrades, which write the reports to
`/var/log/leapp/leapp-reports.txt` and the above report would look like this:
```plain
Risk Factor: high
Title: Unsupported architecture
Summary: Upgrade process is only supported on x86_64 systems.
Key: 8751aa33d13ee9d71823221311cf26f83bd7c2a2
```
and also prints a summary of the reports to the console.

It is possible to verify that the report was generated using the `snactor` tool
to run the actor, passing `--print-output` option this time to output all
generated messages by the actor:

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
To inspect the message.data field, the `jq` tool can be used:

```sh
snactor run CheckSystemArch --verbose --print-output | jq '.[] | .message.data | fromjson'
{
  "report": "{\"audience\": \"sysadmin\", \"groups\": [\"inhibitor\", \"sanity\"], \"severity\": \"high\", \"summary\": \"Upgrade process is only supported on x86_64 systems.\", \"title\": \"Unsupported architecture\"}"
}

```
