from leapp.actors import Actor
from leapp.models import DepCheck1, DepCheck2
from leapp.tags import SecondPhaseTag, WorkflowApiTestWorkflowTag
from leapp.workflows.api.v3 import DepCheckAPI4


class SecondPhaseActor(Actor):
    """
    This is just an actor to ensure no inpact on actors in different phases and that things like non tuple produces
    or consumes are handled properly.
    """

    name = 'second_phase_actor'
    consumes = (DepCheck1)  # On purpose not a tuple
    produces = (DepCheck2)  # On purpose not a tuple
    apis = (DepCheckAPI4)  # On purpose not a tuple
    tags = (SecondPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        pass
