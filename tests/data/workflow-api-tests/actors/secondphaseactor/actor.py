from leapp.actors import Actor
from leapp.tags import SecondPhaseTag, WorkflowApiTestWorkflowTag
from leapp.workflows.api.v3 import DepCheckAPI4


class SecondPhaseActor(Actor):
    """
    This is just an actor to ensure no inpact on actors in different phases. Nothing to do for it here.
    """

    name = 'second_phase_actor'
    consumes = ()
    produces = ()
    apis = (DepCheckAPI4,)
    tags = (SecondPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        pass
