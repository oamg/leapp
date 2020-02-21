import os.path
import subprocess

import py


def test_workflow_api():
    repository_path = py.path.local(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'workflow-api-tests'))
    with repository_path.as_cwd():
        subprocess.check_call(['snactor', 'workflow', 'run', '--debug', 'WorkflowAPITest'])
