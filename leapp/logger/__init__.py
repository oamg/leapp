import datetime
import logging
import logging.config
import os
import time
import sys

from leapp.utils.audit import Audit
_logger = None


class LeappAuditHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(LeappAuditHandler, self).__init__(*args, **kwargs)
        self.use_remote = kwargs.pop('use_remote', False)
        if self.use_remote:
            from leapp.utils.actorapi import get_actor_api
            self.url = 'leapp://localhost/actors/v1/log'
            self.session = get_actor_api()

    def emit(self, record):
        log_data = {
            'event': 'log-message',
            'context': os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'),
            'stamp': datetime.datetime.utcnow().isoformat() + 'Z',
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
        from leapp.utils.actorapi import RequestException
        try:
            self.session.post(self.url, json=log_data, timeout=0.1)
        except RequestException:
            pass


def configure_logger():
    global _logger
    if not _logger:
        path = os.getenv('LEAPP_LOGGER_CONFIG', '/etc/leapp/logger.conf')
        if path and os.path.isfile(path):
            logging.config.fileConfig(path)
        else: # Fall back logging configuration
            logging.Formatter.converter = time.gmtime
            log_format = '%(asctime)s.%(msecs)-3d %(levelname)-8s PID: %(process)d %(name)s: %(message)s'
            log_date_format = '%Y-%m-%d %H:%M:%S'
            logging.basicConfig(
                level=logging.DEBUG if os.getenv('LEAPP_DEBUG', '1') == '1' else logging.INFO,
                format=log_format,
                datefmt=log_date_format,
                stream=sys.stderr,
            )
            logging.getLogger('urllib3').setLevel(logging.WARN)
            handler = LeappAuditHandler()
            handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))
            logging.getLogger('leapp').addHandler(handler)

        _logger = logging.getLogger('leapp')
        _logger.info('Logging has been initialized')

    return _logger
