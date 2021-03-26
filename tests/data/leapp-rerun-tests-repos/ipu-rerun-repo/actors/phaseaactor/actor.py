from leapp.actors import Actor
from leapp.tags import InplaceUpgradeWorkflowTag, PhaseATag


class PhaseAActor(Actor):
    """
    No documentation has been provided for the phase_a_actor actor.
    """

    name = 'phase_a_actor'
    consumes = ()
    produces = ()
    tags = (InplaceUpgradeWorkflowTag, PhaseATag)

    def process(self):
        print('<<<TEST>>>: {}'.format(self.__class__.__name__))
