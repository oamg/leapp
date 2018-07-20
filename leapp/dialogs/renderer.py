import six


if six.PY2:
    input = raw_input  # noqa
else:
    from builtins import input  # noqa


class DialogRendererBase(object):
    """ Base class for all renderer implementations """

    def __init__(self):
        pass

    def render(self, dialog):
        """
        Renders the given dialog

        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        raise NotImplementedError()


class CommandlineRenderer(DialogRendererBase):
    """
    CommandlineRenderer implements the handling for commandline user interactions.
    """
    def __init__(self):
        from getpass import getpass
        self.getpass = getpass

    def render(self, dialog):
        """
        Renders the given dialog

        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        if dialog.title:
            self._render_title(dialog.title)
        if dialog.reason:
            self._render_reason(dialog.reason)
        for component in dialog.components:
            if component.value is None:
                # Only render questions we don't know the answer of
                component.dispatch(self, dialog)

    @staticmethod
    def _render_title(value):
        print('\n{}:\n{}\n'.format(value, (len(value) + 1) * '='))

    @staticmethod
    def _render_reason(value):
        print(value + '\n')

    def _render_label(self, value, min_label_width, underline=None):
        line = self._format_label(value, min_label_width).strip()
        print(line)
        if underline:
            print(underline * len(line))

    @staticmethod
    def _format_label(value, min_label_width, default=None):
        if default is None:
            default = ''
        else:
            default = ' [{}]'.format(default)
        return ('{value: >' + str(min_label_width + 2) + 's}').format(value=value + default + ': ')

    def render_password_component(self, component, dialog):
        """
        Renders the password component

        :param component: The password component to render
        :type component: leapp.dialogs.components.PasswordComponent
        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        dialog.answer(component, self.getpass(prompt=self._format_label(component.label or 'Password: ',
                                              min_label_width=dialog.min_label_width)))

    def render_text_component(self, component, dialog):
        """
        Renders the text component

        :param component: The text component to render
        :type component: leapp.dialogs.components.TextComponent
        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        return self._render_text_component(component, dialog)

    def _render_text_component(self, component, dialog, result_hook=None, default_hint=None):
        if default_hint is None:
            default_hint = component.default
        while True:
            result = input(
                self._format_label(component.label, default=default_hint, min_label_width=dialog.min_label_width))
            if not result and component.default is not None:
                result = component.default
            elif result and result_hook:
                if result_hook(component, dialog, result):
                    break
                continue
            elif not result:
                continue
            dialog.answer(component, result)
            break

    def render_choice_component(self, component, dialog):
        """
        Renders the choices component

        :param component: The choices component to render
        :type component: leapp.dialogs.components.ChoicesComponent
        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        if not component.choices:
            return
        indices = '0123456789abcdefghijklmnopqrstuvwxyz'
        selected = set()
        if component.multi and component.default:
            selected = set(component.default)
        while True:
            self._render_label(component.label, min_label_width=dialog.min_label_width, underline='-')
            for idx, choice in enumerate(component.choices):
                checked = ''
                if component.multi:
                    checked = ' [{}] '.format('X' if idx in selected else ' ')
                print('   {answer}. {checked}{label}'.format(answer=indices[idx], label=choice, checked=checked))
            default = ''
            if component.default is not None:
                default = ' [{}]'.format(component.default)
            if component.multi:
                label = 'Which entry to toggle (Empty response to continue)'
            else:
                label = 'Choice{default}'.format(default=default)
            result = input(self._format_label(label, len(label)))
            if component.multi:
                if not result:
                    dialog.answer(component, tuple(sorted(selected)))
                    break
                elif len(result) == 1 and -1 < indices.index(result) < len(component.choices):
                    idx = indices.index(result)
                    if idx in selected:
                        selected.remove(idx)
                    else:
                        selected.add(idx)
            else:
                if not result and component.default is not None:
                    dialog.answer(component, component.default)
                    break
                elif len(result) == 1 and -1 < indices.index(result) < len(component.choices):
                    dialog.answer(component, indices.index(result))
                    break

    def render_multiple_choice_component(self, component, dialog):
        """
        Renders the multiple choices component

        :param component: The multiple choices component to render
        :type component: leapp.dialogs.components.MultipleChoiceComponent
        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        self.render_choice_component(component, dialog)

    def render_bool_component(self, component, dialog):
        """
        Renders the boolean component for displaying Yes/No questions

        :param component: The boolean component to render
        :type component: leapp.dialogs.components.BooleanComponent
        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        default_hint = '{}/{}'.format(*component.values)
        if component.default is not None:
            if component.default:
                default_hint = component.values[0]
            else:
                default_hint = component.values[1]
        self._render_text_component(component, dialog, result_hook=self._bool_result_hook,
                                    default_hint=default_hint)

    def render_number_component(self, component, dialog):
        """
        Renders the number component

        :param component: The number component to render
        :type component: leapp.dialogs.components.NumberComponent
        :param dialog: The dialog to render
        :type dialog: leapp.dialogs.dialog.Dialog
        :return: None
        """
        self._render_text_component(component, dialog, result_hook=self._int_result_hook)

    @staticmethod
    def _int_result_hook(component, dialog, result):
        try:
            dialog.answer(component, int(result))
            return True
        except ValueError:
            return False

    @staticmethod
    def _bool_result_hook(component, dialog, result):
        true_value = component.values[0].lower()
        false_value = component.values[1].lower()

        valid_values = (true_value, false_value)
        true_values = true_value,

        if false_value[0] != true_value[0]:
            valid_values += (false_value[0], true_value[0])
            true_values += true_value[0],

        result = result.lower()
        valid = result in valid_values
        if valid:
            dialog.answer(component, result in true_values)
        return valid
