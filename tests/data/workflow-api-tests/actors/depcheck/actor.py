from leapp.actors import Actor
from leapp.exceptions import StopActorExecutionError
from leapp.tags import FirstPhaseTag, WorkflowApiTestWorkflowTag
from leapp.workflows.api.v3 import DepCheckAPI1, DepCheckAPI2, DepCheckAPI3, DepCheckAPI4


class DepCheck(Actor):
    """
    This actor verifies the Depedencies APIs to be working as intended.

    DepCheckAPI1 and DepCheckAPI3 consume DepCheck1 and DepCheck3 messages.
    DepCheckAPI2 and DepCheckAPI4 produce DepCheck2 and DepCheck4 messages.

    DepCheckAPI4 requires DepCheckAPI3
    DepCheckAPI3 requires DepCheckAPI2
    DepCheckAPI2 requires DepCheckAPI1

    Therefore by requiring DepCheckAPI4 automatically all 4 DepCheckAPI variants
    are used to amend the consumes and produces fields of the actor.

    Please Note: This is purely a test to ensure that this is the case.
    I highly recommend instead of relying on the dependencies, that each actor
    exactly writes what APIs it uses.
    """

    name = 'dep_check'
    consumes = ()
    produces = ()
    apis = (DepCheckAPI4,)  # A no no normally, be explicit what you use, however for this test it's necessary
    tags = (FirstPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        api1 = DepCheckAPI1()
        if len(api1.consume()) != 1:
            raise StopActorExecutionError(
                "Expected 1 result from DepCheckAPI1.consume => {}".format(len(api1.consume())))

        api2 = DepCheckAPI2()
        api2.produce()

        api3 = DepCheckAPI3()
        if len(api3.consume()) != 2:
            raise StopActorExecutionError(
                "Expected 2 results from DepCheckAPI3.consume => {}".format(len(api3.consume())))

        api4 = DepCheckAPI4()
        api4.produce()
