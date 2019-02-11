from leapp.dialogs import components

class Question(object):
    def __init__(self, component):
        self.component = component

    def make_component(self, key=None):
        self.component.key = key or self.component.key
        return self.component


class Text(Question):
    def __init__(self, label, default=None, help=None):
        super(Text, self).__init__(
            components.TextComponent(
                key=None,
                label=label,
                description=help,
                default=default
            )
        )


class Number(Question):
    def __init__(self, label, default=None, help=None):
        super(Number, self).__init__(
            components.NumberComponent(
                key=None,
                label=label,
                description=help,
                default=default
            )
        )


class YesNo(Question):
    def __init__(self, label, default=None, help=None):
        super(YesNo, self).__init__(
            components.BooleanComponent(
                key=None,
                label=label,
                description=help,
                default=default
            )
        )


class Password(Question):
    def __init__(self, label, default=None, help=None):
        super(Password, self).__init__(
            components.PasswordComponent(
                key=None,
                label=label,
                description=help,
                default=default
            )
        )


class Choice(Question):
    def __init__(self, label, choices, default=None, help=None):
        super(Choice, self).__init__(
            components.ChoiceComponent(
                key=None,
                label=label,
                choices=choices,
                description=help,
                default=default
            )
        )


class MultipleChoice(Question):
    def __init__(self, label, choices, default=None, help=None):
        super(MultipleChoice, self).__init__(
            components.MultipleChoiceComponent(
                key=None,
                label=label,
                choices=choices,
                description=help,
                default=default
            )
        )
