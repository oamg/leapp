import os

from leapp.actors import Actor
from leapp.tags import FirstPhaseTag, UnitTestWorkflowTag
from leapp.exceptions import StopActorExecution, StopActorExecutionError


class ExitStatusActor(Actor):
    name = 'exit_status_actor'
    description = 'No description has been provided for the exit_status_actor actor.'
    consumes = ()
    produces = ()
    tags = (FirstPhaseTag, UnitTestWorkflowTag)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
        if not self.configuration or self.configuration.value != 'unit-test':
            self.report_error('Unit test failed due missing or invalid workflow provided configuration')

        if os.environ.get('ExitStatusActor-Error') == 'StopActorExecution':
            self.report_error('Unit test requested StopActorExecution error')
            raise StopActorExecution

        if os.environ.get('ExitStatusActor-Error') == 'StopActorExecutionError':
            self.report_error('Unit test requested StopActorExecutionError error')
            raise StopActorExecutionError('StopActorExecutionError message')

        if os.environ.get('ExitStatusActor-Error') == 'UnhandledError':
            self.report_error('Unit test requested unhandled error')
            assert 0 == 1, '0 == 1'
