from __future__ import print_function

import datetime
import os
import uuid

import py
import pytest

import leapp.utils.audit
from leapp.messaging.inprocess import InProcessMessaging
from leapp.repository.scan import scan_repo


@pytest.fixture(scope='module')
def repository(leapp_forked):  # noqa; pylint: disable=unused-argument
    repository_path = py.path.local(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'deprecation-tests'))
    with repository_path.as_cwd():
        repo = scan_repo('.')
        repo.load(resolve=True)
        yield repo


def test_deprecations(repository):
    start = datetime.datetime.utcnow()
    actor = repository.lookup_actor('DeprecationTests')
    messaging = InProcessMessaging()
    os.environ['LEAPP_EXECUTION_ID'] = str(uuid.uuid4())
    with py.path.local(actor.directory).as_cwd():
        actor(messaging=messaging).run()
    entries = leapp.utils.audit.get_audit_entry('deprecation', os.getenv('LEAPP_EXECUTION_ID'))
    assert entries
    entries = [entry for entry in entries
               if datetime.datetime.strptime(entry['stamp'].rstrip('Z'), '%Y-%m-%dT%H:%M:%S.%f') > start]
    assert entries and len(entries) == 5
