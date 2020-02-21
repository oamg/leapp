from leapp.actors import Actor
from leapp.exceptions import StopActorExecutionError
from leapp.tags import FirstPhaseTag, WorkflowApiTestWorkflowTag
from leapp.workflows.api.v1 import TestAPI


class ApiV1Test(Actor):
    """
    This actor will check that the testing API ApiV3Test is behaving as expected.
    """

    name = 'api_v1_test'
    consumes = ()
    produces = ()
    apis = (TestAPI,)
    tags = (FirstPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        api = TestAPI()
        # Expected output is always the order a, b, c
        # The parameter order here also is however a, b, c
        if api.order_change(1, 2, 3) != (1, 2, 3):
            raise StopActorExecutionError("order change API failure")

        # Expected is that the input is prefixed with 'survivor.v3.'
        if api.survivor("APIV1Test") != "survivor.v3.APIV1Test":
            raise StopActorExecutionError("v1 survivor test failure")

        # Ensure removed is available and works (Doesn't really do anything just ensures not to have an exception)
        api.removed("ApiV1Test calls removed method")
