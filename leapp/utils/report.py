import json

from leapp.reporting import Remediation
from leapp.utils.audit import get_messages


def fetch_upgrade_report_messages(context_id):
    """
    :param context_id: ID to identify the needed messages
    :type context_id: str
    :return: All upgrade messages of type "Report" withing the given context
    """
    report_msgs = get_messages(names=['Report'], context=context_id) or []

    messages = []
    for message in report_msgs:
        data = message['message']['data']
        report = json.loads(json.loads(data).get('report'))
        messages.append(report)

    return messages


def generate_report_file(messages_to_report, context, path):
    if path.endswith(".txt"):
        with open(path, 'w') as f:
            for message in messages_to_report:
                is_inhibitor = 'inhibitor' in message.get('flags', [])
                f.write('Risk Factor: {}{}\n'.format(message['severity'], ' (inhibitor)' if is_inhibitor else ''))
                f.write('Title: {}\n'.format(message['title']))
                f.write('Summary: {}\n'.format(message['summary']))
                remediation = Remediation.from_dict(message.get('detail', {}))
                if remediation:
                    f.write('Remediation: {}\n'.format(remediation))
                f.write('-' * 40 + '\n')
    elif path.endswith(".json"):
        with open(path, 'w') as f:
            json.dump({'entries': messages_to_report, 'leapp_run_id': context}, f, indent=2)
