from leapp.actors import Actor
from leapp.tags import FifthPhaseTag, UnitTestWorkflowTag


class FifthActor(Actor):
    name = 'fifth_actor'
    description = 'No description has been provided for the fifth_actor actor.'
    consumes = ()
    produces = ()
    tags = (FifthPhaseTag, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
