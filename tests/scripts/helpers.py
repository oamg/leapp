import os
from subprocess import check_call

import pytest

TESTING_PROJECT_NAME = 'testing'


def make_project_dir(name, project_name=TESTING_PROJECT_NAME, scope='session'):
    @pytest.fixture(scope=scope, name=name)
    def impl(request, tmpdir_factory):
        old_value = os.environ.get('LEAPP_CONFIG', None)

        if old_value is not None:
            def fin():
                os.environ['LEAPP_CONFIG'] = old_value
            request.addfinalizer(fin)

        root = tmpdir_factory.mktemp('repositories')
        with root.as_cwd():
            check_call(['snactor', 'repo', 'new', project_name])
            project = root.join(project_name)
            os.environ['LEAPP_CONFIG'] = project.join('.leapp', 'leapp.conf').strpath
            return project
    return impl


project_dir = make_project_dir('project_dir')
