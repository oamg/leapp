from leapp.actors import Actor
from leapp.tags import SecondPhaseTag, UnitTestWorkflowTag
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent, ChoiceComponent, NumberComponent, TextComponent


class DialogActor(Actor):
    name = 'dialog_actor'
    description = 'No description has been provided for the dialog_actor actor.'
    consumes = ()
    produces = ()
    tags = (SecondPhaseTag, UnitTestWorkflowTag)
    dialogs = (Dialog(
        scope='unique_dialog_scope',
        reason='Confirmation',
        components=(
            TextComponent(
                key='text',
                label='text',
                description='a text value is needed',
            ),
            BooleanComponent(key='bool', label='bool', description='a boolean value is needed'),
            NumberComponent(key='num', label='num', description='a numeric value is needed'),
            ChoiceComponent(
                key='choice',
                label='choice',
                description='need to choose one of these choices',
                choices=('One', 'Two', 'Three', 'Four', 'Five'),
            ),
        ),
    ),)

    def process(self):
        from leapp.libraries.common.test_helper import log_execution
        log_execution(self)
        self.get_answers(self.dialogs[0]).get('confirm', False)
