from leapp.models import Model, fields
from leapp.topics import ReportTopic
from leapp.libraries.stdlib.api import produce
import json


class Renderers(Model):
    """
    Model for describing renderers to be used when presenting reports.
    """

    topic = ReportTopic

    html = fields.String()
    """
    Render report message as html
    """
    plaintext = fields.String()
    """
    Render report message as plaintext
    """


class Report(Model):
    """
    Framework model used for reporting and presentation (see "renderers" field) purposes. The report can also carry
    a special meaning using "flags" field.
    """

    __non_inheritable__ = True

    topic = ReportTopic

    severity = fields.StringEnum(choices=['low', 'medium', 'high'])
    """
    Severity of the report entry
    """

    title = fields.String()
    """
    Title of the report entry
    """

    detail = fields.JSON()
    """
    Detail of the report entry as JSON data
    """

    renderers = fields.Model(Renderers)
    """
    :class:`Renderers` describe how to render this report entry
    """

    audience = fields.List(fields.StringEnum(choices=['developer', 'sysadmin']))
    """
    Who is the main audience of this report entry
    """

    flags = fields.List(fields.StringEnum(choices=['inhibitor']))
    """
    Flags can give a special meaning to each report entry, currently supported flags:

        inhibitor - This report entry will inhibit the upgrade process
    """


def report(title=None, detail=None, renderers=None, audience=None, flags=None, severity=None):
    """
    Create and produce a report entry

    For more information about the arguments, please refer to the :class:`Report` model

    :param title: Title of the report message
    :type title: str
    :param detail: Report message details
    :type detail: dict
    :param renderers: Available report entry renderers (e.g. html / plaintext)
    :type renderers: dict
    :param audience: Target audience of the report
    :type audience: list
    :param flags: Functionality flags (e.g. inhibitor)
    :type flags: list
    :param severity: Report severity
    :type severity: str
    """

    # set some healthy defaults
    audience = audience or ['sysadmin']
    severity = severity or 'medium'
    flags = flags or []

    renderers = Renderers(**renderers)
    report_entry = {
        'title': title,
        'detail': detail,
        'renderers': renderers,
        'severity': severity,
        'flags': flags,
        'audience': audience,
    }

    if 'title' in report_entry['detail']:
        raise ValueError('Key "title" cannot be present in the report "detail" structure')

    produce(Report(**report_entry))
