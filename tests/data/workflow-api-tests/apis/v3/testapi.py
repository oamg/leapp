from leapp.workflows.api import WorkflowAPI


class TestAPI(WorkflowAPI):
    """
    V3 implementation of the TestAPI
    """

    def order_change(self, b, c, a):
        """ 'Latest implementation' of the api """
        print("v3.TestAPI.order_change => " + str((a, b, c)))
        # Returns a, b, c as promised
        return a, b, c

    def survivor(self, value):
        """ The actual prefixing implementation """
        print("v3.TestAPI.survivor")
        # Prefixes the value and returns it
        return "survivor.v3." + value
