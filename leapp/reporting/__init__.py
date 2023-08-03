import datetime
import json
import hashlib
import logging
import os
import six

from leapp.compat import string_types
from leapp.models import fields, Model, ErrorModel
from leapp.topics import ReportTopic
from leapp.libraries.stdlib.api import produce
from leapp.utils.deprecation import deprecated


class Report(Model):
    """
    Framework model used for reporting
    """

    __non_inheritable__ = True

    topic = ReportTopic

    report = fields.JSON()


def _add_to_dict(data, path, value, leaf_list=False, flat_list=False):
    for p in path[:-1]:
        if p not in data:
            data[p] = {}
        data = data[p]

    if leaf_list:
        list_val = [value]
        if flat_list and isinstance(value, list):
            list_val = value
        data[path[-1]] = data.get(path[-1], []) + list_val
    else:
        if path[-1] in data:
            raise ValueError('Path {} is already taken'.format('.'.join(path)))
        data[path[-1]] = value


class BasePrimitive(object):
    """
    Report primitive (field) base class for dict targets (implies unique path)
    """
    # deepest nested key in resulting report dict
    name = ''

    def __init__(self, value=None):
        if not isinstance(value, string_types):
            raise TypeError('Value of "{}" must be a string'.format(self.__class__.__name__))
        self._value = value

    @property
    def value(self):
        """Return report field value"""
        return self._value

    @property
    def path(self):
        """Return report field destination path (nested dict description)"""
        return (self.name, )

    def to_dict(self):
        return {self.name: self._value}

    def apply(self, report):
        """Add report entry to the report dict based on provided path"""
        _add_to_dict(report, self.path, self.value, leaf_list=False)


class BaseListPrimitive(BasePrimitive):
    """
    Report primitive (field) base class for list targets (we append value to a list)
    """

    def apply(self, report):
        """Add report entry to the report dict based on provided path"""
        _add_to_dict(report, self.path, self.value, leaf_list=True, flat_list=True)


class Title(BasePrimitive):
    """Report title"""
    name = 'title'


class Summary(BasePrimitive):
    """Report summary"""
    name = 'summary'


class Severity(BasePrimitive):
    """Report severity"""
    name = 'severity'

    INFO = 'info'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

    def __init__(self, value=None):
        severities = (self.INFO, self.LOW, self.MEDIUM, self.HIGH)
        if value not in severities:
            raise ValueError('Severity should be one of: "{}"'.format(' '.join(severities)))
        self._value = value


class Audience(BasePrimitive):
    """Target audience of the report"""
    name = 'audience'

    def __init__(self, value=None):
        if not isinstance(value, string_types):
            raise TypeError('Value of "Audience" must be a string')
        audiences = ('sysadmin', 'developer')
        if value not in audiences:
            raise ValueError('Audience should be one of: "{}"'.format(' '.join(audiences)))
        self._value = value


class Groups(BaseListPrimitive):
    """Report groups."""
    name = 'groups'

    INHIBITOR = 'inhibitor'
    # This is used for framework error reports
    # Reports indicating failure in actors should use the FAILURE group
    _ERROR = 'error'
    FAILURE = 'failure'
    ACCESSIBILITY = 'accessibility'
    AUTHENTICATION = 'authentication'
    BOOT = 'boot'
    COMMUNICATION = 'communication'
    DESKTOP = 'desktop environment'
    DRIVERS = 'drivers'
    EMAIL = 'email'
    ENCRYPTION = 'encryption'
    FILESYSTEM = 'filesystem'
    FIREWALL = 'firewall'
    HIGH_AVAILABILITY = 'high availability'
    KERNEL = 'kernel'
    MONITORING = 'monitoring'
    NETWORK = 'network'
    OS_FACTS = 'OS facts'
    POST = 'post'
    PUBLIC_CLOUD = 'public cloud'
    PYTHON = 'python'
    REPOSITORY = 'repository'
    RHUI = 'rhui'
    SANITY = 'sanity'
    SECURITY = 'security'
    SELINUX = 'selinux'
    SERVICES = 'services'
    TIME_MANAGEMENT = 'time management'
    TOOLS = 'tools'
    UPGRADE_PROCESS = 'upgrade process'

    def __init__(self, value=None):
        if not isinstance(value, list):
            raise TypeError('Value of "Groups" must be a list')
        self._value = value


@deprecated(
    since='2022-08-23',
    message=(
        'The primitive is deprecated as Tags and Flags have been joined into the Groups primitive.'
        'Please use Groups for report message typing instead.'
    )
)
class Tags(Groups):
    def __init__(self, *args, **kwargs):
        super(Tags, self).__init__(*args, **kwargs)


@deprecated(
    since='2022-08-23',
    message=(
        'The primitive is deprecated as Tags and Flags have been joined into the Groups primitive.'
        'Please use Groups for report message typing instead.'
    )
)
class Flags(Groups):
    def __init__(self, *args, **kwargs):
        super(Flags, self).__init__(*args, **kwargs)


# To allow backwards-compatibility with previous report-schema
# Groups that match _DEPRECATION_FLAGS will be shown as flags, the rest as tags
_DEPRECATION_FLAGS = [Groups.INHIBITOR, Groups.FAILURE]

# NOTE(mmatuska): this a temporary solution until Groups._ERROR in the json report-schema
# is altered to account for this addition of Groups_ERROR
_UPCOMING_DEPRECATION_FLAGS = [Groups._ERROR]


class Key(BasePrimitive):
    """Stable identifier for report entries."""
    name = 'key'

    def __init__(self, uuid):
        # uuid is allowed to be string or unicode only, checking in py2/py3 friendly mode
        if not isinstance(uuid, six.string_types):
            raise ValueError('Key value should be a string.')

        self._value = uuid


class ExternalLink(BaseListPrimitive):
    """External link report detail field"""
    name = 'external'

    def __init__(self, url=None, title=None):
        if not all(isinstance(v, string_types) for v in (url, title)):
            raise TypeError('Values "url" and "title" of "ExternalLink" must be a string')
        self._value = {'url': url, 'title': title}

    @property
    def path(self):
        return ('detail', 'external')


class RelatedResource(BaseListPrimitive):
    """Report detail field for related resources (e.g. affected packages/files)"""
    name = 'related_resources'

    def __init__(self, scheme=None, identifier=None):
        if not all(isinstance(v, string_types) for v in (scheme, identifier)):
            raise TypeError('Values "scheme" and "identifier" of "RelatedResource" must be a string')
        self._value = {'scheme': scheme, 'title': identifier}

    @property
    def path(self):
        return ('detail', 'related_resources')


class BaseRemediation(BaseListPrimitive):
    """Remediation base class"""
    name = 'remediations'

    @property
    def path(self):
        return ('detail', 'remediations')


def _guarantee_encoded_str(text, encoding='utf-8'):
    """Guarantees that result is a utf-8 encoded string"""
    # Apply conversion only in py2 case
    if six.PY3:
        return text
    # Unless data is already encoded -> encode it
    try:
        return text.encode(encoding)
    except (UnicodeDecodeError, AttributeError):
        return text


def _guarantee_decoded_str(text, encoding='utf-8'):
    """Guarantees that result is 'native' text"""
    # Apply conversion only in py2 case
    if six.PY3:
        return text
    # Unless data is already decoded -> decode it
    try:
        return text.decode(encoding)
    except (UnicodeEncodeError, AttributeError):
        return text


class RemediationCommand(BaseRemediation):
    def __init__(self, value=None):
        if not isinstance(value, list):
            raise TypeError('Value of "RemediationCommand" must be a list')
        self._value = {'type': 'command', 'context': [_guarantee_decoded_str(c) for c in value]}

    def __repr__(self):
        # NOTE(ivasilev) As the message can contain non-ascii characters let's deal with it properly.
        # As per python practices repr has to return an encoded string
        return "[{}] {}".format(self._value['type'],
                                ' '.join([_guarantee_encoded_str(c) for c in self._value['context']]))


class RemediationHint(BaseRemediation):
    def __init__(self, value=None):
        self._value = {'type': 'hint', 'context': _guarantee_decoded_str(value)}

    def __repr__(self):
        # NOTE(ivasilev) As the message can contain non-ascii characters let's deal with it properly.
        # As per python practices repr has to return an encoded string
        return "[{}] {}".format(self._value['type'], _guarantee_encoded_str(self._value['context']))


class RemediationPlaybook(BaseRemediation):
    def __init__(self, value=None):
        self._value = {'type': 'playbook', 'context': _guarantee_decoded_str(value)}

    def __repr__(self):
        # NOTE(ivasilev) As the message can contain non-ascii characters let's deal with it properly.
        # As per python practices repr has to return an encoded string
        return "[{}] {}".format(self._value['type'], _guarantee_encoded_str(self._value['context']))


class Remediation(object):
    def __init__(self, playbook=None, commands=None, hint=None):
        self._remediations = []
        if hint:
            self._remediations.append(RemediationHint(value=hint))
        if commands:
            for command in commands:
                self._remediations.append(RemediationCommand(value=command))
        if playbook:
            self._remediations.append(RemediationPlaybook(value=playbook))

    def apply(self, report):
        for remediation in self._remediations:
            remediation.apply(report)

    def __repr__(self):
        return "\n".join([repr(r) for r in self._remediations])

    def to_dict(self):
        return {'remediations': [r.to_dict() for r in self._remediations]}

    @classmethod
    def from_dict(cls, data):
        values = data.get('remediations', [])
        playbook = next((v['context'] for v in values if v['type'] == 'playbook'), None)
        hint = next((v['context'] for v in values if v['type'] == 'hint'), None)
        commands = [v['context'] for v in values if v['type'] == 'command']
        if values:
            return Remediation(playbook, commands, hint)


def _sanitize_entries(entries):
    if not any(isinstance(e, Title) for e in entries):
        raise ValueError('Title not provided in the report.')
    if not any(isinstance(e, Summary) for e in entries):
        raise ValueError('Summary not provided in the report.')
    if not any(isinstance(e, Severity) for e in entries):
        entries.append(Severity('info'))
    if not any(isinstance(e, Audience) for e in entries):
        entries.append(Audience('sysadmin'))
    _check_stable_key(entries, raise_if_undefined=os.getenv('LEAPP_DEVEL_FIXED_REPORT_KEY', '0') != '0')


def _check_stable_key(entries, raise_if_undefined=False):
    """
    Inserts a Key into the entries of the report if it doesn't exist.

    The resulting id is calculated from the mandatory report
    entries (severity, audience, title).
    Please note that the original entries list is modified.
    """
    def _find_entry(cls):
        entry = next((e for e in entries if isinstance(e, cls)), None)
        if entry:
            return entry._value

    logger = logging.getLogger('leapp.reporting')
    key = _find_entry(Key)
    if key is not None:
        # Key is already there, check that it's not an empty string
        if not key.strip():
            logger.error('An empty string is specified as Key')
            raise ValueError('Key can not be an empty string.')
        return

    if raise_if_undefined:
        raise ValueError('Stable Key report entry with specified unique value not provided')

    # No Key found - let's generate one!
    key_str = u'{severity}:{audience}:{title}'.format(severity=_find_entry(Severity),
                                                      audience=_find_entry(Audience),
                                                      title=_find_entry(Title))
    key_value = hashlib.sha1(key_str.encode('utf-8')).hexdigest()
    entries.append(Key(key_value))
    logger.warning('Stable Key report entry not provided, dynamically generating one - {}'.format(key_value))


def _create_report_object(entries):
    report = {}

    _sanitize_entries(entries)
    for entry in entries:
        entry.apply(report)

    if Groups.INHIBITOR in report.get('groups', []):
        if Groups._ERROR in report.get('groups', []):
            # *error != inhibitor*
            msg = ('Only one of Groups._ERROR and Groups.INHIBITOR can be set at once.'
                   ' Maybe you were looking for Groups.FAILURE?')
            raise ValueError(msg)

        # Before removing Flags, the original inhibitor detection worked
        # by checking the `flags` field; keep the `flags` field until we drop Flags completely
        # Currently we know that 'flags' does not exist otherwise so it's
        # safe to just set it
        report['flags'] = [Groups.INHIBITOR]
    if Groups._ERROR in report.get('groups', []):
        # see above for explanation
        report['flags'] = [Groups._ERROR]

    return Report(report=report)


def create_report(entries):
    """
    Produce final report message
    """
    produce(_create_report_object(entries))


_DEPRECATION_SEVERITY_THRESHOLD = datetime.timedelta(days=180)


def create_report_from_deprecation(deprecation):
    """
    Convert deprecation json to report json
    """
    since = datetime.datetime.strptime(deprecation['since'], '%Y-%m-%d').date()

    severity = Severity.MEDIUM
    if since < (datetime.date.today() - _DEPRECATION_SEVERITY_THRESHOLD):
        severity = Severity.HIGH

    report = _create_report_object([
        Title('{message} at {filename}:{lineno}'.format(
            message=deprecation['message'].split('\n')[0],
            filename=deprecation['filename'],
            lineno=deprecation['lineno'])),
        Severity(severity),
        Audience('developer'),
        Summary('{reason}\nSince: {since}\nLocation: {filename}:{lineno}\nNear: {line}'.format(
            reason=deprecation['reason'],
            since=deprecation['since'],
            filename=deprecation['filename'],
            lineno=deprecation['lineno'],
            line=deprecation['line']
        )),
    ])
    return json.loads(report.dump()['report'])


def create_report_from_error(error_dict):
    """
    Convert error json to report json
    """
    error = ErrorModel.create(error_dict)
    entries = [
        Title(error.message),
        Summary(error.details or ""),
        Severity('high'),
        Audience('sysadmin'),
        Groups([Groups._ERROR])
    ]
    report = _create_report_object(entries)
    return json.loads(report.dump()['report'])
