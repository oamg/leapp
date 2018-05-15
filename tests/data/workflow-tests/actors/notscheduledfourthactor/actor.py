from leapp.actors import Actor
from leapp.tags import FourthPhaseTag


class NotScheduledFourthActor(Actor):
    name = 'not_scheduled_fourth_actor'
    description = 'No description has been provided for the not_scheduled_fourth_actor actor.'
    consumes = ()
    produces = ()
    tags = (FourthPhaseTag,)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
