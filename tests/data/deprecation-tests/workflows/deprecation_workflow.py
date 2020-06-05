from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import DeprecationWorkflowTag, DeprecationPhaseTag


class DeprecationWorkflow(Workflow):
    name = 'DeprecationWorkflow'
    tag = DeprecationWorkflowTag
    short_name = 'deprecation_workflow'
    description = '''No description has been provided for the DeprecationWorkflow workflow.'''

    class PhaseName(Phase):
        name = 'deprecation_phase'
        filter = TagFilter(DeprecationPhaseTag)
        policies = Policies(Policies.Errors.FailPhase,
                            Policies.Retry.Phase)
        flags = Flags()
