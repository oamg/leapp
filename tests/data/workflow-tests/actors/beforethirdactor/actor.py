from leapp.actors import Actor
from leapp.tags import ThirdPhaseTag, UnitTestWorkflowTag


class BeforeThirdActor(Actor):
    name = 'before_third_actor'
    description = 'No description has been provided for the before_third_actor actor.'
    consumes = ()
    produces = ()
    tags = (ThirdPhaseTag.Before, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
