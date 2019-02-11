from leapp.utils.meta import with_metaclass
import leapp.dialogs.components
from leapp.dialogs.questions import Question


class DialogMeta(type):
    def __new__(mcs, name, bases, attrs):
        klass = super(DialogMeta, mcs).__new__(mcs, name, bases, attrs)
        klass.scope = name.lower()
        if getattr(klass, '__doc__', None):
            klass.reason = klass.__doc__.strip()
        for attr_name, attr in attrs.items():
            if isinstance(attr, Question):
                klass.components += (attr.make_component(key=attr_name),)
        return klass


class Dialog(with_metaclass(DialogMeta)):
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

    def __init__(self, scope=None, reason=None, title=None, components=None):
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
        self.title = title or self.title
        self.scope = scope or self.scope
        self.reason = reason or self.reason
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

    def request_answers(self, store, renderer):
        """
        :param store: AnswerStore instance
        :param renderer: Target renderer instance
        :return: Dictionary with answers once retrieved
        """
        def make_component(component):
            component = component.copy()
            value = component.pop('value', None)
            component.pop('value_type', None)
            comp = getattr(leapp.dialogs.components, component.pop('class_type'))(**component)
            comp.value = value
            return comp

        used_comps = (comp if isinstance(comp, leapp.dialogs.components.Component) else make_component(comp) for comp in self.components)
        if any([component.value is None for component in used_comps]):
            self._store = store
            renderer.render(self)
            self._store = None
        return dict(store.get(self.scope, {}))
