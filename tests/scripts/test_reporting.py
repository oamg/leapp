from collections import namedtuple
import datetime

import pytest

from leapp.reporting import (
    _add_to_dict,
    _DEPRECATION_SEVERITY_THRESHOLD,
    create_report_from_deprecation,
    create_report_from_error,
    _create_report_object,
    Audience, Key, Title, Summary, Severity, RelatedResource
)


ReportPrimitive = namedtuple('ReportPrimitive', ['data', 'path', 'value', 'is_leaf_list'])

leaf_is_dict = ReportPrimitive({}, ('summary',), 'We better fix this!', False)
leaf_is_list = ReportPrimitive({}, ('summary',), 'We better fix this!', False)

path_taken = ReportPrimitive({'summary': 'Fix is coming!'}, ('summary',), 'We better fix this!', False)

leaf_list_append1 = ReportPrimitive(
    {}, ('detail', 'remediation'), {'type': 'hint', 'context': 'Read the docs!'}, True
)
leaf_list_append2 = ReportPrimitive(
    {}, ('detail', 'remediation'), {'type': 'command', 'context': 'man leapp'}, True
)


def value_from_path(data, path):
    value = data
    for p in path:
        if isinstance(value, dict) and value.get(p, None):
            value = value[p]
        else:
            return None
    return value


def is_path_valid(data, path):
    return bool(value_from_path(data, path))


def assert_leaf_list(data, path, is_leaf_list):
    res = isinstance(value_from_path(data, path), list)
    if is_leaf_list:
        assert res
    else:
        assert not res


@pytest.mark.parametrize('primitive', (leaf_is_dict, leaf_is_list))
def test_add_to_dict_func_leaves(primitive):
    data, path, value, is_leaf_list = primitive

    _add_to_dict(data, path, value, is_leaf_list)
    assert is_path_valid(data, path)
    assert_leaf_list(data, path, is_leaf_list)


def test_add_to_dict_func_path_taken():
    data, path, value, is_leaf_list = path_taken

    with pytest.raises(ValueError):
        _add_to_dict(data, path, value, is_leaf_list)


def test_add_to_dict_func_append():
    data, path, value, is_leaf_list = leaf_list_append1

    _add_to_dict(data, path, value, is_leaf_list)
    assert is_path_valid(data, path)
    assert_leaf_list(data, path, is_leaf_list)

    # we do not want data again as we will re-use the dict for appending
    _data, path, value, is_leaf_list = leaf_list_append2
    _add_to_dict(data, path, value, is_leaf_list)

    assert is_path_valid(data, path)
    assert_leaf_list(data, path, is_leaf_list)
    assert len(value_from_path(data, path)) == 2


def test_convert_from_error_to_report():
    error_dict_no_details = {
        'message': 'The system is not registered or subscribed.',
        'time': '2019-11-19T05:13:04.447562Z',
        'details': None,
        'actor': 'verify_check_results',
        'severity': 'error'}
    report = create_report_from_error(error_dict_no_details)
    assert report['severity'] == 'high'
    assert report['title'] == 'The system is not registered or subscribed.'
    assert report['audience'] == 'sysadmin'
    assert report['summary'] == ''
    error_dict_with_details = {
        'message': 'The system is not registered or subscribed.',
        'time': '2019-11-19T05:13:04.447562Z',
        'details': 'Some other info that should go to report summary',
        'actor': 'verify_check_results',
        'severity': 'error'}
    report = create_report_from_error(error_dict_with_details)
    assert report['severity'] == 'high'
    assert report['title'] == 'The system is not registered or subscribed.'
    assert report['audience'] == 'sysadmin'
    assert report['summary'] == 'Some other info that should go to report summary'
    # make sure key argument is there
    error_dict_key_not_specified = {
        'message': 'The system is not registered or subscribed.',
        'time': '2019-11-19T05:13:04.447562Z',
        'details': 'Some other info that should go to report summary',
        'actor': 'verify_check_results',
        'severity': 'error'}
    report = create_report_from_error(error_dict_key_not_specified)
    assert "key" in report


def test_create_report_from_deprecation():
    curr_date = datetime.datetime.today()
    old_date = curr_date - _DEPRECATION_SEVERITY_THRESHOLD - datetime.timedelta(days=1)

    for (since, severity) in ((curr_date, 'medium'), (old_date, 'high')):
        data = {
            'message': 'Usage of deprecated Model "DeprecatedModel"',
            'filename': '/etc/leapp/repos.d/system_upgrade/el7toel8/actors/fooactor/actor.py',
            'line': '        self.produce(DeprecatedModel(foo=bar))\n',
            'lineno': 51,
            'since': since.strftime('%Y-%m-%d'),
            'reason': 'The DeprecatedModel has been deprecated.'}
        report = create_report_from_deprecation(data)
        # I do not want to just copy-paste the code from the function, so let's
        # do the check in this way
        assert data['message'] in report['title']
        assert '{}:{}'.format(data['filename'], data['lineno']) in report['title']
        assert '{}:{}'.format(data['filename'], data['lineno']) in report['summary']
        assert report['severity'] == severity
        assert report['audience'] == 'developer'
        assert data['reason'] in report['summary']
        assert data['since'] in report['summary']
        assert data['line'] in report['summary']
        # make sure key argument is there
        assert 'key' in report


def test_create_report_stable_key(monkeypatch):
    report_entries1 = [Title('Some report title'), Summary('Some summary not used for dynamical key generation'),
                       Audience('sysadmin')]
    report_entries2 = [Title('Some report title'),
                       Summary('Another summary not used for dynamical key generation'), Audience('sysadmin')]
    report_entries_with_severity = [Title('Some report title'),
                                    Summary('Another summary not used for dynamical key generation'),
                                    Severity('high')]
    report_entries_with_audience = [Title('Some report title'),
                                    Summary('Another summary not used for dynamical key generation'),
                                    Audience('developer')]
    report_entries_fixed_key = [Title('Some report title'), Summary('Different summary'), Key('42')]
    report_entries_dialog1 = [Title('Some report title'), RelatedResource('dialog', 'unanswered_section'),
                              Audience('sysadmin'), Summary('Summary')]
    report_entries_dialog_key_set = [Title('Some report title'), RelatedResource('dialog', 'unanswered_section'),
                                     RelatedResource('dialog', 'another_unanswered_section'), Audience('sysadmin'),
                                     Summary('Summary'), Key('dialogkey42')]
    report1 = _create_report_object(report_entries1)
    report2 = _create_report_object(report_entries2)
    report_with_severity = _create_report_object(report_entries_with_severity)
    report_with_audience = _create_report_object(report_entries_with_audience)
    report_fixed_key = _create_report_object(report_entries_fixed_key)
    report_dialog1 = _create_report_object(report_entries_dialog1)
    report_dialog_key_set = _create_report_object(report_entries_dialog_key_set)
    # check that all reports have key field
    for report in [report1, report2, report_with_severity, report_with_audience, report_fixed_key]:
        assert "key" in report.report
    # check that reports with same title but different summary have same dynamically generated key
    assert report1.report["key"] == report2.report["key"]
    # check that entries different in severity only will have different generated keys
    assert report2.report["severity"] != report_with_severity.report["severity"]
    assert report2.report["key"] != report_with_severity.report["key"]
    # check that entries different in audience only will have different generated keys
    assert report2.report["audience"] != report_with_audience.report["audience"]
    assert report2.report["key"] != report_with_audience.report["key"]
    # check that key from provided Key entry is taken
    assert report_fixed_key.report["key"] == "42"
    # check that specific dialog related resources are not considered in key generation
    assert report_dialog1.report["key"] == report1.report["key"]
    # check that providing a key for the dialog report is a solution
    assert report_dialog1.report["key"] != report_dialog_key_set.report["key"]
    assert report_dialog_key_set.report["key"] == "dialogkey42"
    # check that if LEAPP_DEVEL_FIXED_REPORT_KEY is set and there is no key in the report - a ValueError is raised
    monkeypatch.setenv('LEAPP_DEVEL_FIXED_REPORT_KEY', '1')
    with pytest.raises(ValueError):
        _create_report_object([Title('A title'), Summary('A summary')])
