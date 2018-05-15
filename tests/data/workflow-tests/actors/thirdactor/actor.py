from leapp.actors import Actor
from leapp.tags import ThirdPhaseTag, UnitTestWorkflowTag


class ThirdActor(Actor):
    name = 'third_actor'
    description = 'No description has been provided for the third_actor actor.'
    consumes = ()
    produces = ()
    tags = (ThirdPhaseTag, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
