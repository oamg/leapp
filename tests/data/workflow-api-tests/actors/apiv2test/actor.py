from leapp.actors import Actor
from leapp.tags import FirstPhaseTag, WorkflowApiTestWorkflowTag
from leapp.workflows.api.v2 import TestAPI


class ApiV2Test(Actor):
    """
    This actor will check that the testing API ApiV3Test is behaving as expected.
    """

    name = 'api_v2_test'
    consumes = ()
    produces = ()
    apis = (TestAPI,)
    tags = (FirstPhaseTag, WorkflowApiTestWorkflowTag)

    def process(self):
        api = TestAPI()
        # Expected output is always the order a, b, c
        # The parameter order here is however c, b, a
        if api.order_change(3, 2, 1) != (1, 2, 3):
            raise StopActorExecutionError("order change API failure")

        # Expected is that the input is prefixed with 'survivor.v3.'
        if api.survivor("APIV2Test") != "survivor.v3.APIV2Test":
            raise StopActorExecutionError("v2 survivor test failure")
