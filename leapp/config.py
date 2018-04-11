import functools
import re

from six.moves import configparser
from leapp.snactor.utils import find_project_basedir
import os


_LEAPP_CONFIG = None
_CONFIG_DEFAULTS = {
    'database': {
        'path': '/var/lib/leapp/leapp.db',
    },
    'repositories': {
        'global_repo_path': '.',
        'custom_repo_path': None,
    },
}


class BetterConfigParser(configparser.ConfigParser):
    _EINTERPOL = re.compile(r"\$\{([^}]+)\}")

    def get(self, section, *args, **kwargs):
        depth = kwargs.pop('depth', configparser.MAX_INTERPOLATION_DEPTH)
        return self._resolve(BetterConfigParser.__bases__[0].get(self, section, *args, **kwargs),
                             depth=depth,
                             section=section)

    def _resolve(self, value, depth, section):
        if depth:
            if '${' not in value:
                return value
            replacer = functools.partial(self._sub_interpol, depth=depth, section=section)
            value = BetterConfigParser._EINTERPOL.sub(replacer, value)
        return value

    def _sub_interpol(self, match, depth, section):
        s = match.group(1)
        if not s:
            return match.group()
        parts = s.split(':')
        if len(parts) == 1:
            parts.insert(0, section)
        return self.get(*parts, depth=depth - 1)


def get_config():
    global _LEAPP_CONFIG
    if not _LEAPP_CONFIG:
        project_defaults = {}
        if find_project_basedir('.'):
            project_defaults['project'] = {
                'root_dir': find_project_basedir('.'),
                'state_dir': '${root_dir}/.leapp',
            }
        _LEAPP_CONFIG = BetterConfigParser()
        for section, values in _CONFIG_DEFAULTS.items() + project_defaults.items():
            if not _LEAPP_CONFIG.has_section(section):
                _LEAPP_CONFIG.add_section(section)
            for name, value in values.items():
                _LEAPP_CONFIG.set(section, name, value)
        _LEAPP_CONFIG.read([os.getenv('LEAPP_CONFIG', '/etc/leapp/leapp.conf')])

    return _LEAPP_CONFIG