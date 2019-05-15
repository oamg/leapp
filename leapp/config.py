import functools
import re

from six.moves import configparser
from leapp.utils.repository import find_repository_basedir
import os


_LEAPP_CONFIG = None
_CONFIG_DEFAULTS = {
    'database': {
        'path': '/var/lib/leapp/leapp.db',
    },
    'repositories': {
        'repo_path': '.',
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
        repository_defaults = {}
        if find_repository_basedir(os.environ.get('LEAPP_CONFIG', '.')):
            repository_defaults['repository'] = {
                'root_dir': find_repository_basedir(os.environ.get('LEAPP_CONFIG', '.')),
                'state_dir': '${root_dir}/.leapp',
            }
            # Backwards compatibility for older repositories that still used the 'project' terminology.
            repository_defaults['project'] = repository_defaults['repository']
        _LEAPP_CONFIG = BetterConfigParser()
        for section, values in tuple(_CONFIG_DEFAULTS.items()) + tuple(repository_defaults.items()):
            if not _LEAPP_CONFIG.has_section(section):
                _LEAPP_CONFIG.add_section(section)
            for name, value in values.items():
                if value is not None:
                    _LEAPP_CONFIG.set(section, name, value)
        _LEAPP_CONFIG.read([os.getenv('LEAPP_CONFIG', '/etc/leapp/leapp.conf')])

    return _LEAPP_CONFIG
