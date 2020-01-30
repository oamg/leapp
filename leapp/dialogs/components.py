from leapp.compat import unicode_type


class Component(object):
    """
    Base class for all components
    """
    key = None
    label = None
    description = None
    default = None
    value = None
    reason = None
    value_type = None

    def __init__(self, key=None, label=None, description=None, default=None, reason=None):
        """

        :param key: Unique key within a dialog scope. Needs to be in the format: `[a-zA-Z_][a-zA-Z0-9_]*`
        :param label: Label for the input to print
        :param description: Description what this value is used for.
        :param default: Default value to
        :param reason: The reason why we need this value.
        """
        self.key = key or type(self).key
        self.label = label or type(self).label
        self.description = description or type(self).description
        self.default = default if default is not None else type(self).default
        self.value = type(self).value
        self.reason = reason or type(self).reason

    def dispatch(self, renderer, dialog):
        raise NotImplementedError()

    def serialize(self):
        """
        :return: Serialized component information
        """
        return {
            'key': self.key,
            'label': self.label,
            'description': self.description,
            'default': self.default,
            'value': self.value,
            'reason': self.reason,
            'value_type': str(self.value_type) if self.value_type else None
        }


class TextComponent(Component):
    """
    TextComponent is a text input component.
    """
    value_type = str

    def dispatch(self, renderer, dialog):
        renderer.render_text_component(self, dialog=dialog)


class PasswordComponent(TextComponent):
    """
    PasswordComponent is a text input component which will use non echoing input when possible (see getpass).
    """

    label = 'Password'
    value_type = str

    def dispatch(self, renderer, dialog):
        renderer.render_password_component(self, dialog=dialog)


class NumberComponent(Component):
    """
    NumberComponent is used for integer inputs.
    """
    value_type = int
    default = -1

    def dispatch(self, renderer, dialog):
        renderer.render_number_component(self, dialog=dialog)


class BooleanComponent(Component):
    """
    BooleanComponent is used for boolean inputs such as Yes/No questions.
    """
    choices = ('True', 'False')
    values = ('Yes', 'No')
    value_type = bool

    def __init__(self, key=None, label=None, description=None, default=None, reason=None, values=None):
        """
        :param key: Unique key within a dialog scope. Needs to be in the format: `[a-zA-Z_][a-zA-Z0-9_]*`
        :param label: Label for the input to print
        :param description: Description what this value is used for.
        :param default: Default value to
        :param reason: The reason why we need this value.
        :param values: Values to use as True and False, first is always True and the second is always False
                       (e.g. Yes/No)
        """
        super(BooleanComponent, self).__init__(key=key, label=label, description=description, default=default,
                                               reason=reason)
        self.values = values or type(self).values

    def dispatch(self, renderer, dialog):
        renderer.render_bool_component(self, dialog=dialog)


class ChoiceComponent(Component):
    """
    ChoiceComponent is used to give a list of options and allows to select one (like a radio button)
    """
    choices = ()
    multi = False
    value_type = unicode_type

    def __init__(self, choices=None, key=None, label=None, description=None, default=None, reason=None):
        """
        :param key: Unique key within a dialog scope. Needs to be in the format: `[a-zA-Z_][a-zA-Z0-9_]*`
        :param label: Label for the input to print
        :param description: Description what this value is used for.
        :param default: Default value to
        :param reason: The reason why we need this value.
        :param choices: Choices that are available to the user
        """
        super(ChoiceComponent, self).__init__(key=key, label=label, description=description, default=default,
                                              reason=reason)
        self.choices = choices or type(self).choices

    def dispatch(self, renderer, dialog):
        renderer.render_choice_component(self, dialog=dialog)


class MultipleChoiceComponent(ChoiceComponent):
    """
    MultipleChoiceComponent is used to give a list of options and allows to select more than one (like checkboxes)
    """
    choices = ()
    multi = True
    value_type = tuple  # indices

    def dispatch(self, renderer, dialog):
        """
        Calls the appropriate rendering implementation on the renderer and passes itself and the dialog instance to it.

        :param renderer: Renderer instance
        :type renderer: :py:class:`leapp.dialogs.renderer.DialogRendererBase`
        :param dialog:
        :return:
        """
        renderer.render_multiple_choice_component(self, dialog=dialog)
