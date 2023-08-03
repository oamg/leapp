import hashlib
import io
import json
import os

import six

from leapp.reporting import (
    _DEPRECATION_FLAGS,
    _UPCOMING_DEPRECATION_FLAGS,
    Groups,
    Remediation,
    Severity,
    create_report_from_error,
    create_report_from_deprecation
)
from leapp.utils.audit import get_messages, get_audit_entry


def _create_reports_from_deprecations(context_id):
    reports = []
    cache = set()
    for entry in get_audit_entry(event='deprecation', context=context_id):
        data = json.loads(entry['data'])

        # Drop duplicates
        _data_dump = json.dumps(data, sort_keys=True).encode('utf-8')
        data_hash = hashlib.sha256(_data_dump).hexdigest()
        if data_hash in cache:
            continue
        cache.add(data_hash)

        # Create the report
        report = create_report_from_deprecation(data)

        sha256 = hashlib.sha256()
        sha256.update(data_hash.encode('utf-8'))
        sha256.update(entry['context'].encode('utf-8'))

        envelope = {
            'timeStamp': entry['stamp'],
            'hostname': os.environ['LEAPP_HOSTNAME'],
            'actor': entry['actor'],
            'id': sha256.hexdigest()
        }
        report.update(envelope)
        reports.append(report)
    return reports


def fetch_upgrade_report_messages(context_id):
    """
    :param context_id: ID to identify the needed messages
    :type context_id: str
    :return: All upgrade messages of type "Report" within the given context
    """
    report_msgs = get_messages(names=['Report', 'ErrorModel'], context=context_id) or []

    messages = []
    for message in report_msgs:
        data = message['message']['data']

        # We need to be able to uniquely identify each message so we compute
        # a hash of: context UUID, message ID in the database and hash of the
        # data section of the message itself
        sha256 = hashlib.sha256()
        sha256.update(message['message']['hash'].encode('utf-8'))
        sha256.update(message['context'].encode('utf-8'))
        sha256.update(str(message['id']).encode('utf-8'))

        envelope = {
            'timeStamp': message['stamp'],
            'hostname': message['hostname'],
            'actor': message['actor'],
            'id': sha256.hexdigest()
        }
        data_json = json.loads(data)
        report = json.loads(data_json.get('report', "{}"))
        if not report:
            # transform Error message to Report message
            report = create_report_from_error(data_json)
        report.update(envelope)
        messages.append(report)

    messages.extend(_create_reports_from_deprecations(context_id))
    return messages


SEVERITY_LEVELS = {
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4
}


def is_inhibitor(message):
    return has_flag_group(message, Groups.INHIBITOR)


def has_flag_group(message, group):
    """
    A helper to check if a message has Group which would have been a Flag before the Tags/Flags merge in 1.2.0
    """
    # NOTE(borrowed from ivasilev) As groups and flags are mutual exclusive, let's not bother with report_schema version
    # and just check both fields for inhibitor presence
    return group in message.get('groups', message.get('flags', []))


def importance(message):
    if has_flag_group(message, Groups._ERROR):
        return -1
    if has_flag_group(message, Groups.INHIBITOR):
        return 0
    return SEVERITY_LEVELS.get(message['severity'], 99)


def generate_report_file(messages_to_report, context, path, report_schema='1.1.0'):
    # NOTE(ivasilev) Int conversion should not break as only specific formats of report_schema versions are allowed
    report_schema_tuple = tuple(int(x) for x in report_schema.split('.'))
    if path.endswith(".txt"):
        with io.open(path, 'w', encoding='utf-8') as f:
            for message in sorted(messages_to_report, key=importance):
                flag = ''
                if has_flag_group(message, Groups._ERROR):
                    flag = '(error)'
                elif has_flag_group(message, Groups.INHIBITOR):
                    flag = '(inhibitor)'

                f.write(u'Risk Factor: {} {}\n'.format(message['severity'], flag))
                f.write(u'Title: {}\n'.format(message['title']))
                f.write(u'Summary: {}\n'.format(message['summary']))
                remediation = Remediation.from_dict(message.get('detail', {}))
                if remediation:
                    # NOTE(ivasilev) Decoding is necessary in case of python2 as remediation is an encoded string,
                    # while io.open expects "true text" input. For python3 repr will return proper py3 str, no
                    # decoding will be needed.
                    # This hassle and clumsiness makes me sad, so suggestions are welcome.
                    remediation_text = 'Remediation: {}\n'.format(remediation)
                    if isinstance(remediation_text, six.binary_type):
                        # This will be true for py2 where repr returns an encoded string
                        remediation_text = remediation_text.decode('utf-8')
                    f.write(remediation_text)
                if report_schema_tuple > (1, 0, 0):
                    # report-schema 1.0.0 doesn't have a stable report key
                    f.write(u'Key: {}\n'.format(message['key']))
                f.write(u'-' * 40 + '\n')
    elif path.endswith(".json"):
        with io.open(path, 'w', encoding='utf-8') as f:
            # Here all possible conversions will take place
            if report_schema_tuple < (1, 1, 0):
                # report-schema 1.0.0 doesn't have a stable report key
                # copy list of messages here not to mess the initial structure for possible further invocations
                messages_to_report = list(messages_to_report)
                for m in messages_to_report:
                    # FIXME(mmatuska): This modifies the messages as list() does shallow copy, more occurrences below
                    m.pop('key')
            if report_schema_tuple < (1, 2, 0):
                # groups were introduced in 1.2.0, before that there was a tags/flags split
                messages_to_report = list(messages_to_report)
                for msg in messages_to_report:
                    groups = msg.pop('groups', [])
                    msg['flags'] = [g for g in groups if g in _DEPRECATION_FLAGS]
                    msg['tags'] = [
                        g for g in groups
                        if g not in _DEPRECATION_FLAGS and g not in _UPCOMING_DEPRECATION_FLAGS
                    ]
            if report_schema_tuple == (1, 2, 0):
                # DEPRECATED: flags, tags
                # NOTE(pstodulk): This is a temporary solution to ensure that
                # flags are not present in the JSON output as we need to re-introduce
                # flags internally to ensure that any inhibitor checks will not
                # be negatively affected until we drop flags and tags completely.
                messages_to_report = list(messages_to_report)
                for msg in messages_to_report:
                    # NOTE(ivasilev) As flags field is created only if there is an inhibitor
                    # a default value to pop has to be specified not to end up with a KeyError
                    msg.pop('flags', None)
            # NOTE(ivasilev) Has to be done in this way (dumps + py2 conversion + write to file instead of json.dump)
            # because of a py2 bug in the json module that can produce a mix of unicode and str objects that will be
            # incompatible with write. https://bugs.python.org/issue13769
            data = json.dumps({'entries': messages_to_report, 'leapp_run_id': context}, indent=2, ensure_ascii=False)
            if isinstance(data, six.binary_type):
                # Note: if messages_to_report is empty, the produced data is str instead of unicode
                # at least one string must be unicode for the json.dumps function to produce actually
                # unicode object.
                data = data.decode('utf-8')
            f.write(data)
            # append the empty new line to be POSIX compatible
            f.write(u'\n')
