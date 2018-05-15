from leapp.actors import Actor
from leapp.tags import ThirdPhaseTag


class AfterCommonThirdActor(Actor):
    name = 'after_common_third_actor'
    description = 'No description has been provided for the after_common_third_actor actor.'
    consumes = ()
    produces = ()
    tags = (ThirdPhaseTag.After.Common,)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
