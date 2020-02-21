from leapp.actors import Actor
from leapp.exceptions import StopActorExecutionError
from leapp.tags import FirstPhaseTag, WorkflowApiTestWorkflowTag
from leapp.workflows.api.v3 import TestAPI


class ApiV3Test(Actor):
    """
    This actor will check that the testing API ApiV3Test is behaving as expected.
    """

    name = 'api_v3_test'
    consumes = ()
    produces = ()
    apis = (TestAPI,)
    tags = (FirstPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        api = TestAPI()
        # Expected output is always the order a, b, c
        # The parameter order here is however b, c, a
        if api.order_change(2, 3, 1) != (1, 2, 3):
            raise StopActorExecutionError("order change API failure")

        # Expected is that the input is prefixed with 'survivor.v3.'
        if api.survivor("APIV3Test") != "survivor.v3.APIV3Test":
            raise StopActorExecutionError("v3 survivor test failure")
