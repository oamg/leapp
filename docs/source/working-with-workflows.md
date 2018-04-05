# Working with Workflows

## Creating a workflow

To create a new workflow first we create a tag with the same name and then the workflow. (Later the snactor tool
will take care of this, for now this is necessary since it's still a TODO)

```shell
$ snactor new-tag Example
$ snactor workflow new Example
```

This will create the Example workflow boilerplate:

```python
from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.filters import Filter
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import ExampleTag


class ExampleWorkflow(Workflow):
    name = 'Example'
    tag =  ExampleTag
    short_name = 'example'
    description = '''No description has been provided for the Example workflow.'''

    # Template for phase definition - The order in which the phase classes are defined
    # within the Workflow class represents the execution order
    #
    # class PhaseName(Phase):
    #    name = 'phase_name'
    #    filter = TagFilter(PhaseTag)
    #    policies = Policies(Policies.Errors.FailPhase,
    #                        Policies.Retry.Phase)
    #    flags = Flags()
```

## Defining workflow phases

To add a phase one simple defines a new sub class within the workflow deriving from Phase.
We will create one phase called ScanPhase which is supposed to be handling all actors which
are defining the tags (ScanTag or ScanTag.Before or ScanTag.After) and ExampleTag or
with either of ScanTag.Common, ScanTag.Common.Before or ScanTag.Common.After

We will set the policies to fail the whole phase, but let all actors run within even if
an actor failed. The retry policy will be set to restart the whole phase from the beginning
when retrying.

The definition of the ScanPhase class: (Note: ScanTag has to be imported)

```python
class ScanPhase(Phase):
	name = 'scan phase'
	filter = TagFilter(ScanTag)
    policies = Policies(Policies.Errors.FailPhase,
                        Policies.Retry.Phase)
    flags = Flags()
```

Now we will define an imaginary reports phase that would process the data produced by
the ScanPhase and create one or more reports.

For this will will choose the ReportsTag to be used.

This time we will make the the phase fail immediately and bail out when one of the actors
fail.
And we disable the retry, this means that this cannot be re-run and has to be restarted from scratch.

The definition of the ReportsPhase class: (Note: ReportsTag has to be imported)

```python
class ReportsPhase(Phase):
	name = 'reports phase'
	filter = TagFilter(ReportsTag)
    policies = Policies(Policies.Errors.FailImmediately,
                        Policies.Retry.Disabled)
    flags = Flags()
```

The whole example workflow now:

```python
from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.filters import Filter
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import ExampleTag, ScanTag, ReportsTag


class ExampleWorkflow(Workflow):
    name = 'Example'
    tag =  ExampleTag
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


## Testing workflow execution

If you would like to test the execution of workflows you can use the snactor tool.

Here the snactor tool is run with the above workflow in the tutorial project which contains the HostnameScanner
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


