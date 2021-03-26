from leapp.actors import Actor
from leapp.tags import InplaceUpgradeWorkflowTag, FirstBootTag, ReRunVerifyOtherTag


class ReRunActorOther(Actor):
    """
    No documentation has been provided for the re_run_actor_other actor.
    """

    name = 're_run_actor_other'
    consumes = ()
    produces = ()
    tags = (InplaceUpgradeWorkflowTag, FirstBootTag, ReRunVerifyOtherTag)

    def process(self):
        print('<<<TEST>>>: {}'.format(self.__class__.__name__))
