import json
import os
from subprocess import check_call, check_output, CalledProcessError

import pytest


def setup_module(m):
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


@pytest.fixture(scope='session')
def project_dir(tmpdir_factory):
    root = tmpdir_factory.mktemp('repositories')
    with root.as_cwd():
        check_call(['snactor', 'new-project', 'testing'])
        return root.join('testing')


def test_discovery(project_dir):
    with project_dir.as_cwd():
        check_call(['snactor', 'discover'])

        # Ensure snactor discover --json returns valid json
        output = check_output(['snactor', 'discover', '--json']).decode('utf-8')
        data = json.loads(output)
        assert 'actors' in data
        assert 'base_dir' in data and project_dir.samefile(data['base_dir'])
        assert 'models' in data
        assert 'project' in data
        assert 'tags' in data
        assert 'topics' in data

    with type(project_dir)(path=project_dir.dirname).as_cwd():
        with pytest.raises(CalledProcessError):
            check_call(['snactor', 'discover'])


def test_new_tag(project_dir):
    with project_dir.as_cwd():
        check_call(['snactor', 'new-tag', 'Test'])
        assert project_dir.join('tags/test.py').check(file=True)
        check_call(['snactor', 'discover'])


def test_new_topic(project_dir):
    with project_dir.as_cwd():
        # We need the topic to be created already for the model
        # So we have to check if it wasn't already created
        if not project_dir.join('topics/test.py').check(file=True):
            check_call(['snactor', 'new-topic', 'Test'])
        assert project_dir.join('topics/test.py').check(file=True)
        check_call(['snactor', 'discover'])


def test_new_model(project_dir):
    # We need the topic to be created already
    if not project_dir.join('topics/test.py').check(file=True):
        test_new_topic(project_dir)
    with project_dir.as_cwd():
        # We need the model to be created already for the actor
        # So we have to check if it wasn't already created
        if not project_dir.join('models/testmodel.py').check(file=True):
            check_call(['snactor', 'new-model', 'TestModel'])
        assert project_dir.join('models/testmodel.py').check(file=True)
        with pytest.raises(CalledProcessError):
            # Now discover should fail due to the missing topic
            check_call(['snactor', 'discover'])
        project_dir.join('models/testmodel.py').write('''
from leapp.models import Model, fields
from leapp.topics import TestTopic


class TestModel(Model):
    topic = TestTopic
    value = fields.String(default='Test value')
''')
        check_call(['snactor', 'discover'])


def test_new_actor(project_dir):
    # We need the model to be created already
    if not project_dir.join('models/testmodel.py').check(file=True):
        test_new_model(project_dir)
    with project_dir.as_cwd():
        check_call(['snactor', 'new-actor', 'Test'])
        assert project_dir.join('actors/test/actor.py').check(file=True)
        with pytest.raises(CalledProcessError):
            check_call(['snactor', 'discover'])
        project_dir.join('actors/test/actor.py').write('''
from leapp.actors import Actor
from leapp.models import TestModel
from leapp.tags import TestTag

class Test(Actor):
    name = 'test'
    description = 'No description has been provided for the test actor.'
    consumes = ()
    produces = (TestModel,)
    tags = (TestTag,)

    def process(self):
        pass
''')
        check_call(['snactor', 'discover'])
