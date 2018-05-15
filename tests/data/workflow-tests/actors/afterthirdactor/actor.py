import os

from leapp.actors import Actor
from leapp.tags import ThirdPhaseTag, UnitTestWorkflowTag


class AfterThirdActor(Actor):
    name = 'after_third_actor'
    description = 'No description has been provided for the after_third_actor actor.'
    consumes = ()
    produces = ()
    tags = (ThirdPhaseTag.After, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
        if os.environ.get('AfterThirdActor-ReportError') == '1':
            self.report_error("Unit test requested error")
