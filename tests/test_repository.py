from argparse import Namespace
from multiprocessing import Queue, Process

import pytest

from leapp.repository.scan import scan_repo
from helpers import make_project_dir
from leapp.snactor.commands.new_actor import cli as new_actor_cmd
from leapp.snactor.commands.new_tag import cli as new_tag_cmd
from leapp.exceptions import LeappRuntimeError


repository_empty_test_project_dir = make_project_dir('empty_repository_dir', scope='module')
repository_test_project_dir = make_project_dir('repository_dir', scope='module')


def test_empty_repo(empty_repository_dir):
    with empty_repository_dir.as_cwd():
        repo = scan_repo(empty_repository_dir.strpath)
        repo.load(resolve=True)
        assert not repo.actors
        assert not repo.files
        assert not repo.models
        assert not repo.tags
        assert not repo.topics
        assert not repo.workflows
        assert not repo.lookup_workflow('Any')
        assert not repo.lookup_actor('Any')


def setup_repo(repository_dir):
    with repository_dir.as_cwd():
        new_tag_cmd(Namespace(tag_name='Test'))
        actor_path = new_actor_cmd(Namespace(
            actor_name='TestActor',
            tag=['TestTag'],
            consumes=[],
            produces=[],
        ))
        type(repository_dir)(actor_path).mkdir('libraries').join('lib.py').write('''from subprocess import call
def do():
    # This must always fail - This function is crashing the actor ;-)
    assert call(['woot-tool']) == 0
        ''')
        type(repository_dir)(actor_path).mkdir('files').join('test.data').write('data')
        tool_path = type(repository_dir)(actor_path).mkdir('tools').join('woot-tool')
        tool_path.write('''#!/bin/bash
echo 'WOOT'
exit 42
''')
        tool_path.chmod(0o755)
        actor_file = type(repository_dir)(actor_path).join('actor.py')
        actor_content = actor_file.read().replace('pass', '''from leapp.libraries.actor.lib import do
        do()''')
        actor_file.write(actor_content)


def test_repo(repository_dir):
    setup_repo(repository_dir)

    def _run_test(repo_path):
        with repo_path.as_cwd():
            repository = scan_repo(repo_path.strpath)
            assert repository
            repository.load(resolve=True)
            from leapp.tags import TestTag
            assert TestTag.__name__ == 'TestTag'
            assert repository.lookup_actor('TestActor')
            with pytest.raises(LeappRuntimeError):
                repository.lookup_actor('TestActor')().run()

    p = Process(target=_run_test, args=(repository_dir,))
    p.start()
    p.join()
    assert p.exitcode == 0
