"""
This module implements some testing APIs for API depdency checks. Ensuring that all consumes and produces are still in
place and the code keeps working as expected.

DepCheckAPI4 depends on DepCheckAPI3
DepCheckAPI3 depends on DepCheckAPI2
DepCheckAPI2 depends on DepCheckAPI1

DepCheckAPI4 Produces: DepCheck4 Inherits: Produces: DepCheck2, Consumes DepCheck1, DepCheck3
   |
   L> DepCheckAPI3 Consumes: DepCheck3 Inherits: Produces: DepCheck2, Consumes DepCheck1
         |
         L> DepCheckAPI2 Produces: DepCheck2 Inherits: Consumes DepCheck1
               |
               L> DepCheckAPI1 Consumes: DepCheck1

"""

from leapp.libraries.stdlib import api
from leapp.models import DepCheck1, DepCheck2, DepCheck3, DepCheck4
from leapp.workflows.api import WorkflowAPI


class DepCheckAPI1(WorkflowAPI):
    consumes = (DepCheck1,)

    def consume(self):
        """ Consumes all DepCheck1 messages and returns them as a list """
        return list(api.consume(DepCheck1))


class DepCheckAPI2(WorkflowAPI):
    apis = (DepCheckAPI1,)
    produces = (DepCheck2,)

    def produce(self):
        """ Produces a DepCheck2 message """
        api.produce(DepCheck2())


class DepCheckAPI3(WorkflowAPI):
    apis = (DepCheckAPI2,)
    # Be explicit about what you consume even though DepCheckAPI1 consumes it already and is a dependency
    consumes = (DepCheck1, DepCheck3)

    def consume(self):
        """ Consumes all DepCheck3 messages and returns them as a list """
        return list(api.consume(DepCheck1, DepCheck3))


class DepCheckAPI4(WorkflowAPI):
    apis = (DepCheckAPI3,)
    produces = (DepCheck4,)

    def produce(self):
        """ Produces a DepCheck4 message """
        api.produce(DepCheck4())
