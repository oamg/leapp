# Working with workflows


## Creating a workflow

To create a new workflow, create a tag with the same name, and then the workflow.

```shell
$ snactor workflow new Example
```

This procedure creates the Example workflow boilerplate:

```python
from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.filters import Filter
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import ExampleWorkflowTag


class ExampleWorkflow(Workflow):
    name = 'Example'
    tag =  ExampleWorkflowTag
    short_name = 'example'
    description = '''No description has been provided for the Example workflow.'''

    # Template for a phase definition. The order in which the phase classes are defined
    # within the Workflow class represents the execution order.
    #
    # class PhaseName(Phase):
    #    name = 'phase_name'
    #    filter = TagFilter(PhaseTag)
    #    policies = Policies(Policies.Errors.FailPhase,
    #                        Policies.Retry.Phase)
    #    flags = Flags()
```

## Defining workflow phases

To add a phase, define a new subclass within the workflow deriving from the Phase class.


We will create a phase called ScanPhase, which is supposed to be handling all actors that
are defining the ScanTag for the phase, and the ExampleWorkflowTag for the workflow.


Phases have policies that control the execution of the workflow. These policies can control
the behavior in case of errors that are reported by actors. Additionally, the retry behavior
can be specified. The retry behavior allows to specify how to recover from failing workflow executions
without having to rerun the whole process or to disable the retry ability entirely. 

In this scenario, we set the policy to fail the whole phase, but let all actors run, even if
one of the actors fails. And for the retry policy, we specify to restart the whole phase from the beginning.

The definition of the ScanPhase class: (Note: ScanTag has to be imported)

```python
class ScanPhase(Phase):
    name = 'scan phase'
    filter = TagFilter(ScanTag)
    policies = Policies(Policies.Errors.FailPhase,
                        Policies.Retry.Phase)
    flags = Flags()
```

Now, we will define an imaginary reports phase that would process the data produced by
the ScanPhase and create one or more reports.

For this, the ReportsTag is used.

This time, we will make the phase fail immediately, and stop the workflow execution once one of the actors fails.
And we disallow the retry by disabling it, which means that the phase cannot be recovered from. This implies that the workflow has to be restarted from the very beginning.

The definition of the ReportsPhase class: (Note: ReportsTag has to be imported)

```python
class ReportsPhase(Phase):
    name = 'reports phase'
    filter = TagFilter(ReportsTag)
    policies = Policies(Policies.Errors.FailImmediately,
                        Policies.Retry.Disabled)
    flags = Flags()
```

The whole example workflow:

```python
from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.filters import Filter
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import ExampleWorkflowTag, ScanTag, ReportsTag


class ExampleWorkflow(Workflow):
    name = 'Example'
    tag =  ExampleWorkflowTag
    short_name = 'example'
    description = '''No description has been provided for the Example workflow.'''

    class ScanPhase(Phase):
        name = 'scan phase'
        filter = TagFilter(ScanTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()

    class ReportsPhase(Phase):
        name = 'reports phase'
        filter = TagFilter(ReportsTag)
        policies = Policies(Policies.Errors.FailImmediately,
                            Policies.Retry.Disabled)
        flags = Flags()
```


## Testing the workflow execution

To test the execution of workflows, use the snactor tool.

The snactor tool is run with the above workflow in the tutorial project, which contains the HostnameScanner
and IpResolver actors.

```shell
$ snactor workflow run Example
2018-04-04 09:23:54.767 INFO     PID: 38687 leapp: Logging has been initialized
2018-04-04 09:23:54.772 INFO     PID: 38687 leapp.repository.tutorial: New repository 'tutorial' initialized at /home/evilissimo/devel/tutorial
2018-04-04 09:23:54.797 INFO     PID: 38687 leapp.workflow: Starting workflow execution: Example - ID: c4615ed9-662b-49c6-8389-19f6128cdac5
2018-04-04 09:23:54.804 INFO     PID: 38687 leapp.workflow: Starting phase scan phase
2018-04-04 09:23:54.805 INFO     PID: 38687 leapp.workflow.scan phase: Starting stage Before of phase scan phase
2018-04-04 09:23:54.811 INFO     PID: 38687 leapp.workflow.scan phase: Starting stage Main of phase scan phase
2018-04-04 09:23:54.813 INFO     PID: 38687 leapp.workflow.scan phase: Executing actor hostname_scanner
2018-04-04 09:23:54.820 INFO     PID: 38695 leapp.workflow.scan phase.hostname_scanner: Starting to scan for the hostname
2018-04-04 09:24:05.153 INFO     PID: 38695 leapp.workflow.scan phase.hostname_scanner: Finished scanning for the hostname, found = actor-developer
2018-04-04 09:24:05.157 INFO     PID: 38687 leapp.workflow.scan phase: Executing actor ip_resolver
2018-04-04 09:24:05.165 INFO     PID: 38696 leapp.workflow.scan phase.ip_resolver: Starting to resolve hostnames
2018-04-04 09:24:10.325 INFO     PID: 38687 leapp.workflow.scan phase: Starting stage After of phase scan phase
2018-04-04 09:24:10.328 INFO     PID: 38687 leapp.workflow: Starting phase reports phase
2018-04-04 09:24:10.330 INFO     PID: 38687 leapp.workflow.reports phase: Starting stage Before of phase reports phase
2018-04-04 09:24:10.332 INFO     PID: 38687 leapp.workflow.reports phase: Starting stage Main of phase reports phase
2018-04-04 09:24:10.334 INFO     PID: 38687 leapp.workflow.reports phase: Starting stage After of phase reports phase
```

## Adding an actor to a workflow

To have an actor added to a specific workflow phase, assign two tags:
1. The workflow tag 
    In the Example workflow above this was the ExampleWorkflowTag.
2. The phase tag
    In case of the ScanPhase it is the ScanTag, in the Reports phase the ReportsTag.

In the actor, the tags field is filled like this:
```python
    tags = (ExampleWorkflowTag, ScanTag)
```

To have an actor added to any workflow when a phase tag is used, add the `.Common` attribute of the tag:

```python
    tags = (ScanTag.Common,)
```



