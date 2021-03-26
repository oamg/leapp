from leapp.actors import Actor
from leapp.tags import InplaceUpgradeWorkflowTag, FirstBootTag, ReRunVerifyTag


class ReRunActor(Actor):
    """
    No documentation has been provided for the re_run_actor actor.
    """

    name = 're_run_actor'
    consumes = ()
    produces = ()
    tags = (InplaceUpgradeWorkflowTag, FirstBootTag, ReRunVerifyTag)

    def process(self):
        print('<<<TEST>>>: {}'.format(self.__class__.__name__))
