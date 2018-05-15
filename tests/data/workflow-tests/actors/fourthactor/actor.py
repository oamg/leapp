from leapp.actors import Actor
from leapp.tags import FourthPhaseTag, UnitTestWorkflowTag


class FourthActor(Actor):
    name = 'fourth_actor'
    description = 'No description has been provided for the fourth_actor actor.'
    consumes = ()
    produces = ()
    tags = (FourthPhaseTag, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
