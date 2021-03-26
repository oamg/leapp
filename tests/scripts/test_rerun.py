import os
import subprocess
import sys

import pytest
from six import PY3


def _evaluate_results(results, *expected):
    if PY3:
        results = results.decode('utf-8')
    expected = set(expected)
    lines = set([line.split()[-1] for line in results.split('\n') if line.startswith('<<<TEST>>>: ')])
    assert lines == expected


_LEAPP_RERUN_CONFIG = None
_LEAPP_DB_PATH = None


def setup_module():
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


@pytest.fixture(autouse=True, scope='module')
def create_rerun_tempdir(tmpdir_factory):
    global _LEAPP_RERUN_CONFIG
    global _LEAPP_DB_PATH
    tmpdir = tmpdir_factory.mktemp('leapp-rerun')
    _LEAPP_DB_PATH = str(tmpdir.join('leapp.db'))
    config = tmpdir.join('leappconfig')
    repo_test_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))), 'data/leapp-rerun-tests-repos')
    _LEAPP_RERUN_CONFIG = str(config)
    config.write('''
[repositories]
repo_path={repo_test_path}

[database]
path={test_data_path}/leapp.db

[archive]
dir={test_data_path}/logs/archive

[files_to_archive]
dir={test_data_path}/logs/archive
files=leapp-upgrade.log,leapp-report.json,leapp-report.txt

[logs]
dir={test_data_path}/logs
files=leapp-upgrade.log,leapp-preupgrade.log

[report]
dir={test_data_path}/logs
files=leapp-report.json,leapp-report.txt
answerfile={test_data_path}/logs/answerfile
userchoices={test_data_path}/logs/answerfile.userchoices
    '''.format(test_data_path=str(tmpdir), repo_test_path=repo_test_path))


def _perform_rerun(tags=(), unsupported=True, run_upgrade=True):

    leapp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                              'data/leapp-rerun-tests-repos/noroot_leapp.py')
    env = {'LEAPP_CONFIG': _LEAPP_RERUN_CONFIG}
    if os.path.exists(_LEAPP_DB_PATH):
        os.unlink(_LEAPP_DB_PATH)
    args = []

    for tag in tags:
        args.extend(['--only-actors-with-tag', tag])

    try:
        os.environ.update(env)
        if run_upgrade:
            subprocess.check_call([sys.executable, leapp_path, 'upgrade'], env=os.environ)
        if unsupported:
            env['LEAPP_UNSUPPORTED'] = '1'
        os.environ.update(env)
        return subprocess.check_output([sys.executable, leapp_path, 'rerun'] + args + ['FirstBoot'], env=os.environ)
    finally:
        os.environ.pop('LEAPP_CONFIG', None)
        os.environ.pop('LEAPP_UNSUPPORTED', None)


def test_leapp_rerun_no_unsupported_environment_var():
    with pytest.raises(subprocess.CalledProcessError):
        _perform_rerun(unsupported=False, run_upgrade=False)


def test_leapp_rerun_no_upgrade():
    with pytest.raises(subprocess.CalledProcessError):
        _perform_rerun(run_upgrade=False)


def test_leapp_rerun_no_parameters():
    result = _perform_rerun(run_upgrade=True)
    _evaluate_results(result, 'FirstBootActor', 'ReRunActor', 'ReRunActorOther')


def test_leapp_rerun_only_actors_with_tag():
    result = _perform_rerun(tags=('ReRunVerifyTag',), run_upgrade=True)
    _evaluate_results(result, 'ReRunActor')


def test_leapp_rerun_only_actors_with_multiple_tags():
    result = _perform_rerun(tags=('ReRunVerifyTag', 'ReRunVerifyOtherTag'), run_upgrade=True)
    _evaluate_results(result, 'ReRunActor', 'ReRunActorOther')


def test_leapp_rerun_only_actors_with_not_used_tag():
    result = _perform_rerun(tags=('NoSuchTag',), run_upgrade=True)
    _evaluate_results(result)
