from subprocess import check_call

import pytest

TESTING_PROJECT_NAME = 'testing'


@pytest.fixture(scope='session')
def project_dir(tmpdir_factory):
    root = tmpdir_factory.mktemp('repositories')
    with root.as_cwd():
        check_call(['snactor', 'new-project', TESTING_PROJECT_NAME])
        return root.join('testing')
