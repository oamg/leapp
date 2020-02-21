from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import FirstPhaseTag, SecondPhaseTag, WorkflowApiTestWorkflowTag


class WorkflowApiTestWorkflow(Workflow):
    name = 'WorkflowAPITest'
    tag = WorkflowApiTestWorkflowTag
    short_name = 'workflow_api_test'
    description = '''No description has been provided for the WorkflowAPITest workflow.'''

    class FirstPhase(Phase):
        name = 'first_phase'
        filter = TagFilter(FirstPhaseTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()

    class SecondPhase(Phase):
        name = 'second_phase'
        filter = TagFilter(SecondPhaseTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()
