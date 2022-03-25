import hashlib
import json
import os

from leapp.reporting import Remediation, Severity, create_report_from_error, create_report_from_deprecation
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
    :return: All upgrade messages of type "Report" withing the given context
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


def importance(message):
    if 'inhibitor' in message.get('flags', []):
        return 0
    return SEVERITY_LEVELS.get(message['severity'], 99)


def generate_report_file(messages_to_report, context, path, report_schema='1.1.0'):
    # NOTE(ivasilev) Int conversion should not break as only specific formats of report_schema versions are allowed
    report_schema_tuple = tuple(int(x) for x in report_schema.split('.'))
    if path.endswith(".txt"):
        with open(path, 'w') as f:
            for message in sorted(messages_to_report, key=importance):
                is_inhibitor = 'inhibitor' in message.get('flags', [])
                f.write('Risk Factor: {}{}\n'.format(message['severity'], ' (inhibitor)' if is_inhibitor else ''))
                f.write('Title: {}\n'.format(message['title']))
                f.write('Summary: {}\n'.format(message['summary']))
                remediation = Remediation.from_dict(message.get('detail', {}))
                if remediation:
                    f.write('Remediation: {}\n'.format(remediation))
                if report_schema_tuple > (1, 0, 0):
                    # report-schema 1.0.0 doesn't have a stable report key
                    f.write('Key: {}\n'.format(message['key']))
                f.write('-' * 40 + '\n')
    elif path.endswith(".json"):
        with open(path, 'w') as f:
            # Here all possible convertions will take place
            if report_schema_tuple < (1, 1, 0):
                # report-schema 1.0.0 doesn't have a stable report key
                # copy list of messages here not to mess the initial structure for possible further invocations
                messages_to_report = list(messages_to_report)
                for m in messages_to_report:
                    m.pop('key')
            json.dump({'entries': messages_to_report, 'leapp_run_id': context}, f, indent=2)
