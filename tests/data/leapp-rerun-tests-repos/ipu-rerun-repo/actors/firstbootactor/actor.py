from leapp.actors import Actor
from leapp.tags import InplaceUpgradeWorkflowTag, FirstBootTag


class FirstBootActor(Actor):
    """
    No documentation has been provided for the first_boot_actor actor.
    """

    name = 'first_boot_actor'
    consumes = ()
    produces = ()
    tags = (InplaceUpgradeWorkflowTag, FirstBootTag)

    def process(self):
        print('<<<TEST>>>: {}'.format(self.__class__.__name__))
