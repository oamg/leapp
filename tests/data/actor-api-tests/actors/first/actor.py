from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent, ChoiceComponent, NumberComponent, TextComponent
from leapp.tags import ActorFileApiTag
from leapp.models import ApiTestConsume, ApiTestProduce


class First(Actor):
    name = 'first'
    description = 'No description has been provided for the first actor.'
    consumes = (ApiTestConsume,)
    produces = (ApiTestProduce,)
    tags = (ActorFileApiTag,)
    dialogs = (
        Dialog(
            scope='first_actor',
            reason='need to test dialogs',
            components=(
                TextComponent(
                    key='text',
                    label='text',
                    description='a text value is needed',
                ),
                BooleanComponent(
                    key='bool',
                    label='bool',
                    description='a boolean value is needed'
                ),
                NumberComponent(
                    key='num',
                    label='num',
                    description='a numeric value is needed'
                ),
                ChoiceComponent(
                    key='choice',
                    label='choice',
                    description='need to choose one of these choices',
                    choices=('One', 'Two', 'Three', 'Four', 'Five'),
                ),
            ),
        ),
    )

    def process(self):
        pass
