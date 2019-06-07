from argparse import Namespace
from multiprocessing import Process

import mock
import pytest

from helpers import make_repository_dir_fixture
from leapp.repository.scan import find_and_scan_repositories, scan_repo
from leapp.snactor.commands.new_actor import cli as new_actor_cmd
from leapp.snactor.commands.new_tag import cli as new_tag_cmd
from leapp.snactor.commands.workflow.new import cli as new_workflow_cmd
from leapp.exceptions import LeappRuntimeError, RepositoryConfigurationError


# override repository_dir fixture generally defined in session scope
repository_test_repository_dir = make_repository_dir_fixture('repository_dir', scope='module')
empty_repodir_fixture = make_repository_dir_fixture(name='empty_repository_dir', scope='module')


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
        new_workflow_cmd(Namespace(name='Test', class_name=None, short_name=None))
        actor_path = new_actor_cmd(Namespace(
            actor_name='TestActor',
            tag=['TestTag', 'TestWorkflowTag'],
            consumes=[],
            produces=[],
        ))
        type(repository_dir)(actor_path).join('tests', 'test_this_actor.py').write('print("I am a test")')
        type(repository_dir)(actor_path).mkdir('libraries').mkdir('lib').join('__init__.py').write(
            '''from subprocess import call
# This is to ensure that actor tools are available on actor library load time
assert call(['woot-tool']) == 42

# This is to ensure that common tools are available on actor library load time
assert call(['common-woot-tool']) == 42

def do():
    # This must always fail - This function is crashing the actor ;-)
    assert call(['woot-tool']) == 0
        ''')
        repository_dir.mkdir('libraries').mkdir('lib').join('__init__.py').write(
            '''from subprocess import call
# This is to ensure that common tools are available on common library load time
assert call(['common-woot-tool']) == 42
        ''')
        type(repository_dir)(actor_path).mkdir('files').join('test.data').write('data')
        repository_dir.mkdir('files').join('common-test.data').write('data')
        tool_path = type(repository_dir)(actor_path).mkdir('tools').join('woot-tool')
        woot_tool_content = '''#!/bin/bash
echo 'WOOT'
exit 42
'''
        tool_path.write(woot_tool_content)
        tool_path.chmod(0o755)
        tool_path = repository_dir.mkdir('tools').join('common-woot-tool')
        tool_path.write(woot_tool_content)
        tool_path.chmod(0o755)
        actor_file = type(repository_dir)(actor_path).join('actor.py')
        actor_content = actor_file.read().replace('pass', '''from leapp.libraries.actor.lib import do
        import leapp.libraries.common.lib

        do()''')
        actor_file.write(actor_content)


def test_repo(repository_dir):
    setup_repo(repository_dir)

    def _run_test(repo_path):
        with repo_path.as_cwd():
            repository = find_and_scan_repositories(repo_path.dirpath().strpath)
            assert repository
            repository.load(resolve=True)
            import leapp.tags
            assert getattr(leapp.tags, 'TestTag')
            assert repository.lookup_actor('TestActor')
            assert repository.lookup_workflow('TestWorkflow')
            assert not repository.lookup_workflow('MissingWorkflow')
            assert not repository.lookup_actor('MissingActor')
            assert repository.repos
            assert len(repository.dump()) >= 1
            assert repository.actors
            assert not repository.topics
            assert not repository.models
            assert repository.tags
            assert repository.workflows
            assert repository.tools
            assert repository.libraries
            assert repository.files
            with pytest.raises(LeappRuntimeError):
                repository.lookup_actor('TestActor')().run()

    p = Process(target=_run_test, args=(repository_dir,))
    p.start()
    p.join()
    assert p.exitcode == 0


def test_find_and_scan_repositories_no_user_repos_config(empty_repository_dir):
    repo_path = empty_repository_dir.dirpath().strpath
    with mock.patch('leapp.repository.manager.RepositoryManager.get_missing_repo_links', return_value={'42'}):
        with mock.patch('leapp.utils.repository.get_global_repositories_data', return_value={}):
            with mock.patch('leapp.utils.repository.get_user_config_repos', return_value='/no/such/file.json'):
                with pytest.raises(RepositoryConfigurationError) as err:
                    find_and_scan_repositories(repo_path, include_locals=True)
                assert 'No repos configured' in err.value.message
