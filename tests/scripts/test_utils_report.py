import datetime
import json

import leapp.utils.report

_CONTEXT = 'some_str'
curr_date = datetime.datetime.today()


def _create_entry(data, event='deprecation', context=_CONTEXT):
    return {
        'id': '1',
        'stamp': '2020-09-11T15:56:23.767457Z',
        'actor': 'actor',
        'hostname': 'hostname',
        'data': json.dumps(data),
        'context': context,
        'event': event,
    }


_AUDIT_DATA = (
    # first two entries should be filtered out
    _create_entry(context='ignore123', data={}),
    _create_entry(event='something', data={}),
    _create_entry({
        'message': 'Usage of deprecated Model "DeprecatedModel"',
        'filename': '/etc/leapp/repos.d/system_upgrade/el7toel8/actors/fooactor/actor.py',
        'line': '        self.produce(DeprecatedModel(foo=bar))\n',
        'lineno': 51,
        'since': curr_date.strftime('%Y-%m-%d'),
        'reason': 'The DeprecatedModel has been deprecated.',
    }),
    # this is one is duplicate of the previous one
    _create_entry({
        'message': 'Usage of deprecated Model "DeprecatedModel"',
        'filename': '/etc/leapp/repos.d/system_upgrade/el7toel8/actors/fooactor/actor.py',
        'line': '        self.produce(DeprecatedModel(foo=bar))\n',
        'lineno': 51,
        'since': curr_date.strftime('%Y-%m-%d'),
        'reason': 'The DeprecatedModel has been deprecated.',
    }),
    _create_entry({
        'message': 'Usage of deprecated Model "DetonatedModel"',
        'filename': '/etc/leapp/repos.d/system_upgrade/el7toel8/actors/fooactor/actor.py',
        'line': '        self.produce(DetonatedModel(foo=bar))\n',
        'lineno': 51,
        'since': curr_date.strftime('%Y-%m-%d'),
        'reason': 'The DetonatedModel has been deprecated.',
    }),
    # to have at least one old entry
    _create_entry({
        'message': 'Usage of deprecated Model "AModel"',
        'filename': '/etc/leapp/repos.d/system_upgrade/el7toel8/actors/fooactor/actor.py',
        'line': '        self.produce(Amodel(foo=bar))\n',
        'lineno': 51,
        'since': '2018-01-01',
        'reason': 'The Amodel has been deprecated.',
    }),
)


def mocked_get_audit_entry(event, context):
    return (entry for entry in _AUDIT_DATA if entry['context'] == context and entry['event'] == event)


def test_create_report_from_deprecations(monkeypatch):
    monkeypatch.setattr(leapp.utils.report, 'get_audit_entry', mocked_get_audit_entry)

    reports = leapp.utils.report._create_reports_from_deprecations(_CONTEXT)
    # no duplicates and only deprecated messages for the given context
    assert len(reports) == len(_AUDIT_DATA) - 3

    for report in reports:
        assert 'Usage of deprecated Model' in report['title']
        assert report['audience'] == 'developer'
        assert report['severity'] in ('high', 'medium')
    assert len([i for i in reports if i['severity'] == 'high']) == 1

    reports = leapp.utils.report._create_reports_from_deprecations('non-existing-context')
    assert not reports
