from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import InplaceUpgradeWorkflowTag, PhaseATag, PhaseBTag, FirstBootTag


class IPUWorkflow(Workflow):
    name = 'IPUWorkflow'
    tag = InplaceUpgradeWorkflowTag
    short_name = 'ipu'
    description = '''No description has been provided for the InplaceUpgrade workflow.'''

    # Template for phase definition - The order in which the phase classes are defined
    # within the Workflow class represents the execution order
    #
    # class PhaseName(Phase):
    #    name = 'phase_name'
    #    filter = TagFilter(PhaseTag)
    #    policies = Policies(Policies.Errors.FailPhase,
    #                        Policies.Retry.Phase)
    #    flags = Flags()

    class PhaseA(Phase):
        name = 'phase_a'
        filter = TagFilter(PhaseATag)
        policies = Policies(Policies.Errors.FailPhase, Policies.Retry.Phase)
        flags = Flags()

    class PhaseB(Phase):
        name = 'phase_b'
        filter = TagFilter(PhaseBTag)
        policies = Policies(Policies.Errors.FailPhase, Policies.Retry.Phase)
        flags = Flags()

    class FirstBoot(Phase):
        name = 'FirstBoot'
        filter = TagFilter(FirstBootTag)
        policies = Policies(Policies.Errors.FailPhase, Policies.Retry.Phase)
        flags = Flags()
