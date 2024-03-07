from leapp.models import UnitTestConfig
from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import UnitTestWorkflowTag, FirstPhaseTag, SecondPhaseTag


class UnitTestWorkflow(Workflow):
    name = 'LeappDBUnitTest'
    tag = UnitTestWorkflowTag
    short_name = 'unit_test'
    description = '''No description has been provided for the UnitTest workflow.'''
    configuration = UnitTestConfig

    class FirstPhase(Phase):
        name = 'first-phase'
        filter = TagFilter(FirstPhaseTag)
        policies = Policies(Policies.Errors.FailImmediately, Policies.Retry.Phase)
        flags = Flags()

    class SecondPhase(Phase):
        name = 'second-phase'
        filter = TagFilter(SecondPhaseTag)
        policies = Policies(Policies.Errors.FailPhase, Policies.Retry.Phase)
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
