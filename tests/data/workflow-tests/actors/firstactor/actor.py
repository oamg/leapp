import os

from leapp.actors import Actor
from leapp.tags import FirstPhaseTag, UnitTestWorkflowTag


class FirstActor(Actor):
    name = 'first_actor'
    description = 'No description has been provided for the first_actor actor.'
    consumes = ()
    produces = ()
    tags = (FirstPhaseTag, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
        if not self.configuration or self.configuration.value != 'unit-test':
            self.report_error('Unit test failed due missing or invalid workflow provided configuration')
        if os.environ.get('FirstActor-ReportError') == '1':
            self.report_error("Unit test requested error")
