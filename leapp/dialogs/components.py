class Component(object):
    key = None
    label = None
    description = None
    default = None
    value = None
    reason = None
    value_type = None

    def __init__(self, key=None, label=None, description=None, default=None, value=None, reason=None):
        self.key = key or type(self).key
        self.label = label or type(self).label
        self.description = description or type(self).description
        self.default = default or type(self).default
        self.value = value or type(self).value
        self.reason = reason or type(self).reason

    def dispatch(self, renderer, dialog):
        raise NotImplementedError()


class TextComponent(Component):
    value_type = str

    def dispatch(self, renderer, dialog):
        renderer.render_text_component(self, dialog=dialog)


class PasswordComponent(TextComponent):
    label = 'Password'
    value_type = str

    def dispatch(self, renderer, dialog):
        renderer.render_password_component(self, dialog=dialog)


class NumberComponent(Component):
    value_type = int
    default = -1

    def dispatch(self, renderer, dialog):
        renderer.render_number_component(self, dialog=dialog)


class BooleanComponent(Component):
    values = ('Yes', 'No')
    value_type = bool

    def dispatch(self, renderer, dialog):
        renderer.render_bool_component(self, dialog=dialog)


class ChoiceComponent(Component):
    choices = ()
    multi = False
    value_type = int  # Index

    def __init__(self, choices=None, key=None, label=None, description=None, default=None, value=None, reason=None):
        super(ChoiceComponent, self).__init__(key=key, label=label, description=description, default=default,
                                              value=value, reason=reason)
        self.choices = choices or type(self).choices

    def dispatch(self, renderer, dialog):
        renderer.render_choice_component(self, dialog=dialog)


class MultipleChoiceComponent(ChoiceComponent):
    choices = ()
    multi = True
    value_type = tuple  # indices

    def __init__(self, choices=None, key=None, label=None, description=None, default=None, value=None, reason=None):
        super(MultipleChoiceComponent, self).__init__(key=key, label=label, description=description, default=default,
                                                      value=value, reason=reason)
        self.choices = choices or type(self).choices

    def dispatch(self, renderer, dialog):
        renderer.render_multiple_choice_component(self, dialog=dialog)
