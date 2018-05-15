import json
import os
import tempfile

import py
import pytest

from leapp.repository.scan import scan_repo


@pytest.fixture(scope='module')
def repository():
    project_path = py.path.local(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'workflow-tests'))
    with project_path.as_cwd():
        repo = scan_repo('.')
        repo.load(resolve=True)
        yield repo


def test_workflow(repository):
    with tempfile.NamedTemporaryFile() as test_log_file:
        os.environ['LEAPP_TEST_EXECUTION_LOG'] = test_log_file.name
        workflow = repository.lookup_workflow('UnitTest')()
        assert not workflow.initial
        assert workflow.phase_actors
        assert not workflow.consumes
        assert not workflow.produces
        workflow.run()
        test_log_file.seek(0)
        order = [json.loads(line)['class_name'] for line in test_log_file]
        assert order.pop(0) == 'FirstActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('SecondActor', 'SecondCommonActor')
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('BeforeCommonThirdActor', 'BeforeThirdActor')
        assert order.pop(0) == 'ThirdActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('AfterCommonThirdActor', 'AfterThirdActor')
        assert order.pop(0) == 'FourthActor'
        assert order.pop(0) == 'FifthActor'
        assert not order


def test_workflow_until_actor(repository):
    with tempfile.NamedTemporaryFile() as test_log_file:
        os.environ['LEAPP_TEST_EXECUTION_LOG'] = test_log_file.name
        workflow = repository.lookup_workflow('UnitTest')()
        workflow.run(context='unit-test-context', until_actor='ThirdActor')
        test_log_file.seek(0)
        order = [json.loads(line)['class_name'] for line in test_log_file]
        assert order.pop(0) == 'FirstActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('SecondActor', 'SecondCommonActor')
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('BeforeCommonThirdActor', 'BeforeThirdActor')
        assert order.pop(0) == 'ThirdActor'
        assert not order


def test_workflow_until_phase_main(repository):
    with tempfile.NamedTemporaryFile() as test_log_file:
        os.environ['LEAPP_TEST_EXECUTION_LOG'] = test_log_file.name
        workflow = repository.lookup_workflow('UnitTest')()
        workflow.run(context='unit-test-context', until_phase='ThirdPhase.main')
        test_log_file.seek(0)
        order = [json.loads(line)['class_name'] for line in test_log_file]
        assert order.pop(0) == 'FirstActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('SecondActor', 'SecondCommonActor')
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('BeforeCommonThirdActor', 'BeforeThirdActor')
        assert order.pop(0) == 'ThirdActor'
        assert not order


def test_workflow_until_phase_before(repository):
    with tempfile.NamedTemporaryFile() as test_log_file:
        os.environ['LEAPP_TEST_EXECUTION_LOG'] = test_log_file.name
        workflow = repository.lookup_workflow('UnitTest')()
        workflow.run(context='unit-test-context', until_phase='ThirdPhase.before')
        test_log_file.seek(0)
        order = [json.loads(line)['class_name'] for line in test_log_file]
        assert order.pop(0) == 'FirstActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('SecondActor', 'SecondCommonActor')
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('BeforeCommonThirdActor', 'BeforeThirdActor')
        assert not order


def test_workflow_until_phase_full(repository):
    with tempfile.NamedTemporaryFile() as test_log_file:
        os.environ['LEAPP_TEST_EXECUTION_LOG'] = test_log_file.name
        workflow = repository.lookup_workflow('UnitTest')()
        workflow.run(context='unit-test-context', until_phase='ThirdPhase')
        test_log_file.seek(0)
        order = [json.loads(line)['class_name'] for line in test_log_file]
        assert order.pop(0) == 'FirstActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('SecondActor', 'SecondCommonActor')
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('BeforeCommonThirdActor', 'BeforeThirdActor')
        assert order.pop(0) == 'ThirdActor'
        assert tuple(sorted([order.pop(0), order.pop(0)])) == ('AfterCommonThirdActor', 'AfterThirdActor')
        assert not order


def test_workflow_skip_phases_until(repository):
    with tempfile.NamedTemporaryFile() as test_log_file:
        os.environ['LEAPP_TEST_EXECUTION_LOG'] = test_log_file.name
        workflow = repository.lookup_workflow('UnitTest')()
        workflow.run(context='unit-test-context', skip_phases_until='ThirdPhase')
        test_log_file.seek(0)
        order = [json.loads(line)['class_name'] for line in test_log_file]
        assert order.pop(0) == 'FourthActor'
        assert order.pop(0) == 'FifthActor'
        assert not order
