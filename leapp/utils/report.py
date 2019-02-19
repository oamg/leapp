import json
import six

from jinja2 import Template

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


def fetch_upgrade_report_messages(context_id, renderer):
    """
    :param context_id: ID to identify the needed messages
    :type context_id: str
    :param renderer: How messages will be rendered (e.g html or plaintext)
    :type context_id: str
    :return: All upgrade messages of type "Report" withing the given context
    """
    report_msgs = get_messages(names=['Report'], context=context_id)

    if report_msgs:
        messages_to_print = []
        for message in report_msgs:
            topic = message.get('topic')
            phase = message.get('phase')
            data = json.loads(message.get('message').get('data'))
            merged_data = {'topic': topic, 'phase': phase}
            merged_data.update({
                'audience': data['audience'],
                'title': data['title'],
                'flags': data['flags'],
                'severity': data['severity']
            })
            detail = _flatten_dict(json.loads(data['detail']))
            merged_data.update(detail)
            template = Template(data['renderers'].get(renderer))
            messages_to_print.append(template.render(merged_data))

        return messages_to_print

    return None
