from leapp.utils.meta import with_metaclass


class PhaseMeta(type):
    classes = []

    def __new__(mcs, name, bases, attrs):
        klass = super(PhaseMeta, mcs).__new__(mcs, name, bases, attrs)
        PhaseMeta.classes.append(klass)
        return klass


class Phase(with_metaclass(PhaseMeta)):
    @classmethod
    def get_index(cls):
        return PhaseMeta.classes.index(cls)
