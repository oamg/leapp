from leapp.actors import Actor
from leapp.tags import InplaceUpgradeWorkflowTag, PhaseBTag


class PhaseBActor(Actor):
    """
    No documentation has been provided for the phase_b_actor actor.
    """

    name = 'phase_b_actor'
    consumes = ()
    produces = ()
    tags = (InplaceUpgradeWorkflowTag, PhaseBTag)

    def process(self):
        print('<<<TEST>>>: {}'.format(self.__class__.__name__))
