import json
import os
import tarfile
import urlparse

from jinja2 import Template
import requests
import six

from leapp.config import get_config
from leapp.utils.audit import get_messages


def _flatten_dict(dict_):
    new_dict = {}
    if type(dict_) is not dict:
        return new_dict

    for k, v in six.iteritems(dict_):
        if type(v) == dict:
            new_dict.update(_flatten_dict(v))
        else:
            new_dict[k] = v

    return new_dict


def fetch_upgrade_report_raw(context_id, renderers=True):
    """
    :param context_id: ID to identify the needed messages
    :type context_id: str
    :param renderers: whether copy or skip renderers field of original message
    :type boolean
    :return: A list of upgrade messages of type "Report" withing the given context,
             each message is a dict of raw data.
    """
    report_msgs = get_messages(names=['Report'], context=context_id) or []

    messages = []
    for message in report_msgs:
        data = json.loads(message.get('message').get('data'))
        merged_data = {
            'topic': message.get('topic'),
            'phase': message.get('phase'),
            'audience': data['audience'],
            'title': data['title'],
            'flags': data['flags'],
            'severity': data['severity']
        }
        if renderers:
            merged_data['renderers'] = data['renderers']
        detail = _flatten_dict(json.loads(data['detail']))
        merged_data.update(detail)
        messages.append(merged_data)

    return messages


def fetch_upgrade_report_messages(context_id, renderer):
    """
    :param context_id: ID to identify the needed messages
    :type context_id: str
    :param renderer: How messages will be rendered (e.g html or plaintext)
    :type renderer: str
    :return: All upgrade messages of type "Report" withing the given context
    """
    messages_raw = fetch_upgrade_report_raw(context_id)
    if not messages_raw:
        # return [] to be consistent?
        return

    messages_to_print = []
    for msg_data in messages_raw:
        template = Template(msg_data.pop('renderers').get(renderer))
        messages_to_print.append(template.render(msg_data))

    return messages_to_print


def upload_to_insights(report_json):
    insights_config = get_config().get('report', 'insights', {})
    username = os.getenv('LEAPP_DEVEL_INSIGHTS_USERNAME', insights_config.get('username', ''))
    password = os.getenv('LEAPP_DEVEL_INSIGHTS_PASSWORD', insights_config.get('password', ''))
    server = os.getenv('LEAPP_DEVEL_INSIGHTS_SERVER', insights_config.get('server', ''))
    upload_endpoint = 'api/ingress/v1/upload'
    report_tar = six.StringIO()
    with tarfile.open(mode='w:gz', fileobj=report_tar) as tar:
        tar.add(report_json)
    url = urlparse.urljoin(server, upload_endpoint)
    res = requests.post(url, auth=(username, password),
                        files={'file': ('preupgrade_report.json',
                                        report_tar.getvalue(),
                                        'application/vnd.redhat.leapp-reporting.preupgradereport+tgz')},
                        verify=False)
    return res.ok, res.text
