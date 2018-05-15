from leapp.actors import Actor
from leapp.tags import SecondPhaseTag, UnitTestWorkflowTag


class SecondActor(Actor):
    name = 'second_actor'
    description = 'No description has been provided for the second_actor actor.'
    consumes = ()
    produces = ()
    tags = (SecondPhaseTag, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
