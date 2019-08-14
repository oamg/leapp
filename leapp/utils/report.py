import json

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
