import os
from subprocess import check_call

import pytest

TESTING_REPOSITORY_NAME = 'testing'


def make_repository_dir(name, repository_name=TESTING_REPOSITORY_NAME, scope='session'):
    @pytest.fixture(scope=scope, name=name)
    def impl(request, tmpdir_factory):
        old_value = os.environ.get('LEAPP_CONFIG', None)

        if old_value is not None:
            def fin():
                os.environ['LEAPP_CONFIG'] = old_value
            request.addfinalizer(fin)

        root = tmpdir_factory.mktemp('repositories')
        with root.as_cwd():
            check_call(['snactor', 'repo', 'new', repository_name])
            repository = root.join(repository_name)
            os.environ['LEAPP_CONFIG'] = repository.join('.leapp', 'leapp.conf').strpath
            return repository
    return impl


repository_dir = make_repository_dir('repository_dir')
