import pytest

from leapp.messaging.inprocess import InProcessMessaging, BaseMessaging
from leapp.models.error_severity import ErrorSeverity
from leapp.models import ErrorModel
from leapp.exceptions import CannotConsumeErrorMessages

from helpers import repository_dir  # noqa: F401; pylint: disable=unused-import
from test_models import UnitTestModel
from test_tags import TestTag


class UnitTestModelUnused(UnitTestModel):
    name = 'UnitTestModelUnused'


class FakeActor(object):
    name = 'Fake-actor'
    consumes = (UnitTestModel,)
    produces = ()
    description = '''No description for a fake actor.'''
    tags = (TestTag.Common,)

    def process(self):
        pass


@pytest.mark.parametrize('stored', (True, False))
def test_messaging_messages(repository_dir, stored):
    with repository_dir.as_cwd():
        msg = InProcessMessaging(stored=stored)
        v = UnitTestModel()
        msg.produce(v, FakeActor())
        consumed = tuple(msg.consume(FakeActor(), UnitTestModel))
        assert len(consumed) == 1
        assert len(msg.messages()) == 1
        assert consumed[0] == v


def test_loading(repository_dir):
    with repository_dir.as_cwd():
        msg = InProcessMessaging()
        with pytest.raises(CannotConsumeErrorMessages):
            msg.load((ErrorModel,))
        msg.load((UnitTestModel,))
        v = UnitTestModel()
        consumed = tuple(msg.consume(FakeActor(), UnitTestModel))
        assert len(consumed) == 1
        assert not msg.messages()
        assert consumed[0] == v

        consumed = tuple(msg.consume(FakeActor(), UnitTestModelUnused))
        assert not consumed
        assert not msg.messages()

        consumed = tuple(msg.consume(FakeActor()))
        assert len(consumed) == 1
        assert not msg.messages()
        assert consumed[0] == v

        consumed = tuple(msg.consume(FakeActor(), UnitTestModelUnused))
        assert not consumed
        assert not msg.messages()


def test_report_error(repository_dir):
    with repository_dir.as_cwd():
        msg = InProcessMessaging()
        msg.report_error('Some error', ErrorSeverity.ERROR, FakeActor(), details=None)
        msg.report_error('Some error with details', ErrorSeverity.ERROR, FakeActor(), details={'foo': 'bar'})
        assert len(msg.errors()) == 2


@pytest.mark.parametrize('stored', (True, False))
def test_not_implemented(repository_dir, stored):
    with repository_dir.as_cwd():
        msg = BaseMessaging(stored=stored)
        if stored:
            with pytest.raises(NotImplementedError):
                msg.report_error('Some error', ErrorSeverity.ERROR, FakeActor(), details=None)
            with pytest.raises(NotImplementedError):
                msg.produce(UnitTestModel(), FakeActor())
        with pytest.raises(NotImplementedError):
            msg.load(FakeActor.consumes)
        msg.consume(FakeActor())
        msg.consume(FakeActor(), UnitTestModel)
        assert not msg.errors()
        assert not msg.messages()
        assert msg.stored == stored
