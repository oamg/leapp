import os
from subprocess import check_call

import pytest

TESTING_PROJECT_NAME = 'testing'


@pytest.fixture(scope='session')
def project_dir(request, tmpdir_factory):
    old_value = os.environ.get('LEAPP_CONFIG', None)

    if old_value is not None:
        def fin():
            os.environ['LEAPP_CONFIG'] = old_value
        request.addfinalizer(fin)

    root = tmpdir_factory.mktemp('repositories')
    with root.as_cwd():
        check_call(['snactor', 'new-project', TESTING_PROJECT_NAME])
        project = root.join(TESTING_PROJECT_NAME)
        os.environ['LEAPP_CONFIG'] = project.join('.leapp', 'leapp.conf').strpath
        return project

