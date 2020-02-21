from leapp.workflows.api import WorkflowAPI
from leapp.workflows.api import v3


class TestAPI(WorkflowAPI):
    """ Implementation of the v2.TestAPI which depends on the v3.TestAPI implementation """
    apis = (v3.TestAPI,)

    def __init__(self):
        # Instance of the v3 API
        self._impl = v3.TestAPI()

    def order_change(self, c, b, a):
        """
        Returns the value of a, b, c as a tuple as implemented in the v3 API
        """
        print("v2.TestAPI.order_change => " + str((a, b, c)))
        # Adjusts the order of parameters based on the V3 api needs and returns the value
        return self._impl.order_change(b, c, a)

    def survivor(self, message):
        """
        Prefixes message and returns it.
        """
        print("v2.TestAPI.survivor")
        # Calls the v3 implementation and returns the value
        return self._impl.survivor(message)
