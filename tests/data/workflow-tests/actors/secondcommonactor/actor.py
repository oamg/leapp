from leapp.actors import Actor
from leapp.tags import SecondPhaseTag


class SecondCommonActor(Actor):
    name = 'second_common_actor'
    description = 'No description has been provided for the second_common_actor actor.'
    consumes = ()
    produces = ()
    tags = (SecondPhaseTag.Common,)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
