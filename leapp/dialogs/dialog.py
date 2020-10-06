class Dialog(object):
    """
    The dialog class is used to declare the information passed to the user and retrieved from the user
    during an interaction.
    """

    components = ()
    """ Components to display in the given order in the dialog """

    title = None
    """ Title of the dialog """

    reason = None
    """ An explanation for what the data in this dialog is needed for. """

    scope = None
    """ Unique scope identifier for the data to be stored in the answer files. Scope + component key is used to
        address values.
    """

    def __init__(self, scope, reason, title=None, components=None, key=None):
        """

        :param scope: Unique scope identifier for the data to be stored in the answer files. Scope + component key
                      is used to address values.
        :type scope: str
        :param reason: An explanation for what the data in this dialog is needed for.
        :type reason: str
        :param title: Title of the dialog
        :type title: str
        :param components: Components to display in the given order in the dialog
        :type components: tuple(leapp.dialogs.components.Component)
        :param key: Key to appear in the dialog-related report entry
        :type key: str
        """
        self.components = components or self.components
        self.title = title
        self.scope = scope
        self.reason = reason
        self.key = key
        self._store = None
        self._min_label_width = None

    def serialize(self):
        """
        :return: Dictionary with the serialized representation of a component
        """
        return {
            'components': [component.serialize() for component in self.components],
            'title': self.title,
            'reason': self.reason,
            'scope': self.scope
        }

    @property
    def answerfile_sections(self):
        return {"{}.{}".format(self.scope, c.key): c.choices for c in self.components}

    @property
    def min_label_width(self):
        """
        :return: Returns the highest number of characters all labels in the dialog have, to help calculating the minimum
                 width the labels should have.
        """
        if not self._min_label_width:
            self._min_label_width = max(len(comp.label) for comp in self.components if comp.label)
        return self._min_label_width

    def answer(self, component, value):
        """
        Implements storing of answers.

        :param component: Component for which the answer is set
        :param value: The answer value
        :return: None
        """
        component.value = value
        self._store.answer(self.scope, component.key, value)

    def component_by_key(self, key):
        """
        Finds the component with the given key

        :param key: Key of the component to return
        :type key: str
        :return: Component found or None
        """
        for component in self.components:
            if component.key == key:
                return component
        return None

    def get_answers(self, store):
        """
        Checks answerstore if an answer is recorded for the dialog.

        :param store: AnswerStore instance
        :return: Dictionary with answers once retrieved
        """
        store.translate(self)
        return dict(store.get(self.scope, {}))

    def request_answers(self, store, renderer):
        """
        Same as get_answers but with interactive retrieval of the answer
        in case no recorded answer found in answerstore.

        :param store: AnswerStore instance
        :param renderer: Target renderer instance
        :return: Dictionary with answers once retrieved
        """
        store.translate(self)
        if any([component.value is None for component in self.components]):
            self._store = store
            renderer.render(self)
            self._store = None
        return dict(store.get(self.scope, {}))
