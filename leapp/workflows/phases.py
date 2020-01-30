from leapp.utils.meta import with_metaclass
from leapp.workflows.flags import Flags
from leapp.workflows.policies import Policies


class PhaseMeta(type):
    classes = []

    def __new__(mcs, name, bases, attrs):
        klass = super(PhaseMeta, mcs).__new__(mcs, name, bases, attrs)
        PhaseMeta.classes.append(klass)
        return klass


class Phase(with_metaclass(PhaseMeta)):
    name = None
    filter = None
    policies = Policies(Policies.Errors.FailPhase,
                        Policies.Retry.Phase)
    flags = Flags()

    @classmethod
    def get_index(cls):
        return PhaseMeta.classes.index(cls)

    @classmethod
    def serialize(cls):
        """
        :return: Dictionary with the serialized representation of the phase
        """
        return {
            'name': cls.name,
            'class_name': cls.__name__,
            'index': cls.get_index(),
            'filter': cls.filter.serialize() if cls.filter else None,
            'policies': cls.policies.serialize(),
            'flags': cls.flags.serialize(),
        }
