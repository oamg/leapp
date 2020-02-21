from leapp.actors import Actor
from leapp.exceptions import StopActorExecutionError
from leapp.models import DepCheck2, DepCheck4
from leapp.tags import FirstPhaseTag, WorkflowApiTestWorkflowTag


class DepCheckConsumes(Actor):
    """
    This actor consumes the Models DepCheck2 and DepCheck4 produced by the DepCheck actor to verify the functionality.
    """

    name = 'dep_check_consumes'
    produces = ()
    consumes = (DepCheck2, DepCheck4)
    tags = (FirstPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        # Only one message is supposed to be produced
        if len(list(self.consume(DepCheck2))) != 1:
            raise StopActorExecutionError(
                "Expected 1 DepCheck2 message => {}".format(len(list(self.consume(DepCheck2)))))

        # Only one message is supposed to be produced
        if len(list(self.consume(DepCheck4))) != 1:
            raise StopActorExecutionError(
                "Expected 1 DepCheck4 message => {}".format(len(list(self.consume(DepCheck4)))))
