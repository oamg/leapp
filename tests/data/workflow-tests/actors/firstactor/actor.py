import os

from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.tags import FirstPhaseTag, UnitTestWorkflowTag


class FirstActor(Actor):
    name = 'first_actor'
    description = 'No description has been provided for the first_actor actor.'
    consumes = ()
    produces = ()
    tags = (FirstPhaseTag, UnitTestWorkflowTag)
    dialogs = (
        Dialog(
            scope='unique_dialog_scope',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Disable a deprecated module?'
                          'If no, the upgrade process will be interrupted.',
                    default=False,
                    description='Module XXX is no longer available '
                                'in RHEL-8 since it was replaced by shiny-metal-XXX.',
                    reason='Leaving this module in system configuration may lock out the system.'
                ),
            )
        ),)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
        if not self.configuration or self.configuration.value != 'unit-test':
            self.report_error('Unit test failed due missing or invalid workflow provided configuration')
        if os.environ.get('FirstActor-ReportError') == '1':
            self.report_error("Unit test requested error")
        self.get_answers(self.dialogs[0]).get('confirm', False)
