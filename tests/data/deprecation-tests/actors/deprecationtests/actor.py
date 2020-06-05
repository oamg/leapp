from leapp.actors import Actor
from leapp.libraries.common.deprecation import (DeprecatedNoInit, DeprecatedNoInitDerived, DeprecatedWithInit,
                                                DeprecatedWithInitDerived, deprecated_function)
from leapp.models import DeprecatedModel, SuppressedDeprecatedModel
from leapp.tags import DeprecationPhaseTag, DeprecationWorkflowTag
from leapp.utils.deprecation import suppress_deprecation, deprecated


def whatever(f):
    def wrapper():
        f()
    return wrapper


@deprecated(since='2011-11-11', message='never to be seen')
@whatever
def foobar():
    pass


@suppress_deprecation(SuppressedDeprecatedModel, foobar)
def test_fun(self):
    self.produce(SuppressedDeprecatedModel())
    foobar()


class DeprecationTests(Actor):
    """
    No documentation has been provided for the deprecation_tests actor.
    """

    name = 'deprecation_tests'
    consumes = ()
    produces = (DeprecatedModel, SuppressedDeprecatedModel)
    tags = (DeprecationWorkflowTag, DeprecationPhaseTag)

    def process(self):
        test_fun(self)
        deprecated_function()
        self.produce(DeprecatedModel())
        DeprecatedNoInit()
        DeprecatedNoInitDerived()
        DeprecatedWithInit()
        DeprecatedWithInitDerived()
