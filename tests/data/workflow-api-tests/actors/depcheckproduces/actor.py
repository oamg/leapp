from leapp.actors import Actor
from leapp.models import DepCheck3, DepCheck1
from leapp.tags import FirstPhaseTag, WorkflowApiTestWorkflowTag


class DepCheckProduces(Actor):
    """
    Produces messages DepCheck1 and DepCheck3 which are going to be consumed by the DepCheckAPI1 and DepCheckAPI3 APIs.
    """

    name = 'dep_check_produces'
    consumes = ()
    produces = (DepCheck1, DepCheck3)
    tags = (FirstPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        self.produce(DepCheck1(), DepCheck3())
