import configparser
import os


_LEAPP_CONFIG = None


def get_config():
    global _LEAPP_CONFIG
    if not _LEAPP_CONFIG:
        _LEAPP_CONFIG = configparser.ConfigParser()
        _LEAPP_CONFIG.read([os.getenv('LEAPP_CONFIG', '/etc/leapp/leapp.conf')])
    return _LEAPP_CONFIG
