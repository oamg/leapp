from leapp.dialogs.components import TextComponent, PasswordComponent, NumberComponent, BooleanComponent, \
    ChoiceComponent, MultipleChoiceComponent
from leapp.dialogs.dialog import Dialog
from leapp.dialogs.renderer import CommandlineRenderer


class UsernamePasswordDialog(Dialog):
    """ Reusable username and password request dialog. """
    title = 'Please enter username and password'
    components = (
        TextComponent(key='username', label='Username', default=None),
        PasswordComponent(key='password', label='Password', default=None)
    )


class MessageDialog(Dialog):
    """ Reusable message dialog. - This sends a message to the user only without any special formatting. """
    title = ''

    def __init__(self, message):
        super(MessageDialog, self).__init__(scope=None, reason=message)


def test():
    CHOICES = ('Horse', 'Mouse', 'Cat', 'Elephant', 'Tiger', 'Lion', 'Unicorn', 'Ghost', 'Robot', 'Mermaid', 'Dr. Who')
    dlg = Dialog(scope='test', reason='Testing capabilities', title='Input Tests', components=(
        TextComponent(key='username', label='Username', default=None),
        PasswordComponent(key='password', label='Password', default=None),
        TextComponent(key='default_value', label='Just another field', default='Value'),
        ChoiceComponent(key='choices_nodefault', label='Choose an option without default', choices=CHOICES),
        ChoiceComponent(key='choices_default', label='Choose an option with default', default=7, choices=CHOICES),
        MultipleChoiceComponent(key='multiple_choices_default', label='Select all suitable options', default=(7,),
                                choices=CHOICES),
        NumberComponent(key='some_number', label='What number you\'d like to use?', default=42),
        BooleanComponent(key='some_bool1', label='Do you really want to continue?', default=True),
        BooleanComponent(key='some_bool2', label='Do you really want to continue?')
    ))
    rdrr = CommandlineRenderer()
    rdrr.render(MessageDialog(message='''Wooohooo what's up bro? All good?\nWe'll see later what's going on!'''))
    rdrr.render(dlg)
    from pprint import pprint
    pprint(dlg.request_answers())
