import datetime
import logging
import logging.config
import os
import sys
import time

from leapp.config import get_config
from leapp.libraries.stdlib.config import is_debug, is_verbose
from leapp.utils.actorapi import get_actor_api, RequestException
from leapp.utils.audit import Audit

_logger = None


class LeappAuditHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(LeappAuditHandler, self).__init__(*args, **kwargs)
        self.use_remote = kwargs.pop('use_remote', False)
        if self.use_remote:
            self.url = 'leapp://localhost/actors/v1/log'
            self.session = get_actor_api()

    def emit(self, record):
        log_data = {
            'event': 'log-message',
            'context': os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'),
            'stamp': datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'hostname': os.environ.get('LEAPP_HOSTNAME', 'localhost'),
            'actor': os.environ.get('LEAPP_CURRENT_ACTOR', ''),
            'phase': os.environ.get('LEAPP_CURRENT_PHASE', ''),
            'log': {
                'level': record.levelname,
                'message': self.format(record)
            }
        }
        if self.use_remote:
            self._remote_emit(log_data)
        else:
            self._do_emit(log_data)

    @staticmethod
    def _do_emit(log_data):
        log_data['data'] = log_data.pop('log', {})
        Audit(**log_data).store()

    def _remote_emit(self, log_data):
        try:
            self.session.post(self.url, json=log_data, timeout=0.1)
        except RequestException:
            pass


def configure_logger(log_file=None):
    global _logger
    if not _logger:
        log_format = '%(asctime)s.%(msecs)-3d %(levelname)-8s PID: %(process)d %(name)s: %(message)s'
        log_date_format = '%Y-%m-%d %H:%M:%S'
        path = os.getenv('LEAPP_LOGGER_CONFIG', '/etc/leapp/logger.conf')

        if path and os.path.isfile(path):
            logging.config.fileConfig(path, disable_existing_loggers=False)
        else:  # Fall back logging configuration
            logging.Formatter.converter = time.gmtime
            logging.basicConfig(
                level=logging.ERROR,
                format=log_format,
                datefmt=log_date_format,
                stream=sys.stderr,
            )
            logging.getLogger('urllib3').setLevel(logging.WARN)
            handler = LeappAuditHandler()
            handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))
            logging.getLogger('leapp').addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(os.path.join(get_config().get('logs', 'dir'), log_file))
            file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))
            file_handler.setLevel(logging.DEBUG)
            logging.getLogger('leapp').addHandler(file_handler)

        if is_verbose():
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(logging.DEBUG if is_debug() else logging.INFO)

        _logger = logging.getLogger('leapp')
        _logger.info('Logging has been initialized')

    return _logger
