from leapp.workflows.api import WorkflowAPI
from leapp.workflows.api import v2


class TestAPI(WorkflowAPI):
    """
    V1 of the TestAPI it also depends on the v2.TestAPI
    """
    apis = (v2.TestAPI,)

    def __init__(self):
        # v2 API instance
        self._impl = v2.TestAPI()

    def order_change(self, a, b, c):
        """
        Returns a tuple in the form of a, b, c
        """
        print("v1.TestAPI.order_change => " + str((a, b, c)))
        # Calls v2 api implementation with the corrected parameter order
        # which then calls the v3 api with the corrected parameter order
        # returning the value received
        return self._impl.order_change(c, b, a)

    def survivor(self, value):
        """
        Prefixes a given value - Passed through to the latest version
        """
        print("v1.TestAPI.survivor")
        # Calls v2 api implementation which then calls the v3 api
        # returning the value received
        return self._impl.survivor(message=value)

    def removed(self, yadda):
        print("v1.TestAPI.removed('{}')".format(yadda))
        print("I am removed in newer versions")
        # Does not really do anything as it is removed in v2 and higher
