import logging

import mock
import pytest

from leapp.repository.actor_definition import ActorDefinition, ActorInspectionFailedError, MultipleActorsError
from leapp.exceptions import UnsupportedDefinitionKindError
from leapp.repository import DefinitionKind

_FAKE_META_DATA = {
    'description': 'Fake Description',
    'class_name': 'FakeActor',
    'name': 'fake-actor',
    'path': 'actors/test',
    'tags': (),
    'config_schemas': (),
    'consumes': (),
    'produces': (),
    'dialogs': (),
    'apis': ()
}


def test_actor_definition(repository_dir):
    with repository_dir.as_cwd(), mock.patch('os.chdir', return_value=None):
        logger = logging.getLogger('leapp.actor.test')
        with mock.patch.object(logger, 'log') as log_mock:
            definition = ActorDefinition('actors/test', '.', log=log_mock)
            for kind in set(DefinitionKind.REPO_WHITELIST + DefinitionKind.ACTOR_WHITELIST):
                if kind in DefinitionKind.ACTOR_WHITELIST:
                    definition.add(kind, '.')
                else:
                    with pytest.raises(UnsupportedDefinitionKindError):
                        definition.add(kind, '.')
                    log_mock.error.assert_called_with(
                        "Attempt to add item type %s to actor that is not supported", kind.name)
                    log_mock.reset_mock()
            with mock.patch('leapp.repository.actor_definition.get_actor_metadata', return_value=_FAKE_META_DATA):
                with mock.patch('leapp.repository.actor_definition.get_actors', return_value=[True]):
                    definition._module = True
                    assert definition.consumes == _FAKE_META_DATA['consumes']
                    assert definition.produces == _FAKE_META_DATA['produces']
                    assert definition.tags == _FAKE_META_DATA['tags']
                    assert definition.config_schemas == _FAKE_META_DATA['config_schemas']
                    assert definition.class_name == _FAKE_META_DATA['class_name']
                    assert definition.dialogs == _FAKE_META_DATA['dialogs']
                    assert definition.name == _FAKE_META_DATA['name']
                    assert definition.description == _FAKE_META_DATA['description']
                    assert definition.apis == _FAKE_META_DATA['apis']
                    dumped = definition.serialize()
                    assert dumped.pop('class_name') == definition.class_name
                    assert dumped.pop('description') == definition.description
                    assert dumped.pop('consumes') == definition.consumes
                    assert dumped.pop('produces') == definition.produces
                    assert dumped.pop('apis') == definition.apis
                    assert dumped.pop('tags') == definition.tags
                    assert dumped.pop('config_schemas') == definition.config_schemas
                    assert dumped.pop('dialogs') == [dialog.serialize() for dialog in definition.dialogs]
                    assert dumped.pop('path') == _FAKE_META_DATA['path']
                    assert dumped.pop('name') == definition.name
                    assert dumped.pop('files') == ('.',)
                    assert dumped.pop('libraries') == ('.',)
                    assert dumped.pop('configs') == ('.',)
                    assert dumped.pop('tests') == ('.',)
                    assert dumped.pop('tools') == ('.',)
                    # Assert to ensure we covered all keys
                    assert not dumped

            with pytest.raises(ActorInspectionFailedError):
                with mock.patch('leapp.repository.actor_definition.get_actors', return_value=[]):
                    definition._discovery = None
                    definition.discover()

            with pytest.raises(ActorInspectionFailedError):
                with mock.patch('leapp.repository.actor_definition.get_actors') as mocked_actors:
                    mocked_actors.side_effect = RuntimeError('Test error')
                    definition._discovery = None
                    definition.discover()

            with pytest.raises(MultipleActorsError):
                with mock.patch('leapp.repository.actor_definition.get_actor_metadata', return_value=_FAKE_META_DATA):
                    with mock.patch('leapp.repository.actor_definition.get_actors', return_value=[True, True]):
                        definition._discovery = None
                        definition.discover()
