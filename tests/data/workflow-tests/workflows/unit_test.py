from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import UnitTestWorkflowTag, FirstPhaseTag, SecondPhaseTag, ThirdPhaseTag, FourthPhaseTag, FifthPhaseTag


class UnitTestWorkflow(Workflow):
    name = 'UnitTest'
    tag =  UnitTestWorkflowTag
    short_name = 'unit_test'
    description = '''No description has been provided for the UnitTest workflow.'''

    class FirstPhase(Phase):
       name = 'first-phase'
       filter = TagFilter(FirstPhaseTag)
       policies = Policies(Policies.Errors.FailPhase,
                           Policies.Retry.Phase)
       flags = Flags()

    class SecondPhase(Phase):
       name = 'second-phase'
       filter = TagFilter(SecondPhaseTag)
       policies = Policies(Policies.Errors.FailPhase,
                           Policies.Retry.Phase)
       flags = Flags()

    class ThirdPhase(Phase):
       name = 'third-phase'
       filter = TagFilter(ThirdPhaseTag)
       policies = Policies(Policies.Errors.FailPhase,
                           Policies.Retry.Phase)
       flags = Flags()

    class FourthPhase(Phase):
       name = 'fourth-phase'
       filter = TagFilter(FourthPhaseTag)
       policies = Policies(Policies.Errors.FailPhase,
                           Policies.Retry.Phase)
       flags = Flags()

    class FifthPhase(Phase):
       name = 'fifth-phase'
       filter = TagFilter(FifthPhaseTag)
       policies = Policies(Policies.Errors.FailPhase,
                           Policies.Retry.Phase)
       flags = Flags()

    # Template for phase definition - The order in which the phase classes are defined
    # within the Workflow class represents the execution order
    #
    # class PhaseName(Phase):
    #    name = 'phase_name'
    #    filter = TagFilter(PhaseTag)
    #    policies = Policies(Policies.Errors.FailPhase,
    #                        Policies.Retry.Phase)
    #    flags = Flags()
