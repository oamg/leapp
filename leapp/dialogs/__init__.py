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


class RawMessageDialog(Dialog):
    """ Reusable message dialog. - This sends a message to the user only without any special formatting. """
    title = ''

    def __init__(self, message):
        super(RawMessageDialog, self).__init__(scope=None, reason=message)

    def request_answers(self, store, renderer):
        """
        :param store: AnswerStore instance
        :param renderer: Target renderer instance
        :return: Dictionary with answers once retrieved
        """
        renderer.render(self)
        return {}
