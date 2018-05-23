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

    def __init__(self, scope, reason, title=None, components=None):
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
        """
        self.components = components or self.components
        self.title = title
        self.scope = scope
        self.reason = reason
        self._answers = {}
        self._min_label_width = None

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
        self._answers[component.key] = value

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

    def request_answers(self, renderer):
        """
        TODO: Implement dispatching of the dialog to be shown to the user when the questions aren't answered.
        TODO: This call should be blocking until answers are made available to the user

        :return: Dictionary with answers once retrieved
        """

        renderer.render(self)
        return dict(self._answers)
