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

_leapp_logger = None


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
        try:
            self.session.post(self.url, json=log_data, timeout=0.1)
        except RequestException:
            pass


def configure_logger(log_file=None):
    """
    Configure loggers as per the description below.

    logger: root
      level: DEBUG
      handler: StreamHandler
        level: based on the debug/verbosity options
      handler: LeappAuditHandler
        level: DEBUG
      logger: urllib3
        level: WARN
      logger: leapp
        level: NOTSET
        handler: FileHandler
          level: DEBUG

    :return: The 'leapp' logger
    """
    global _leapp_logger
    if not _leapp_logger:
        _leapp_logger = logging.getLogger('leapp')

        log_format = '%(asctime)s.%(msecs)-3d %(levelname)-8s PID: %(process)d %(name)s: %(message)s'
        log_date_format = '%Y-%m-%d %H:%M:%S'
        logging.Formatter.converter = time.gmtime

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        path = os.getenv('LEAPP_LOGGER_CONFIG', '/etc/leapp/logger.conf')
        if path and os.path.isfile(path):
            logging.config.fileConfig(path)
        else:  # Fall back logging configuration
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))
            stderr_handler.setLevel(logging.ERROR)
            root_logger.addHandler(stderr_handler)

            logging.getLogger('urllib3').setLevel(logging.WARN)

            audit_handler = LeappAuditHandler()
            audit_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))
            audit_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(audit_handler)

        if log_file:
            file_handler = logging.FileHandler(os.path.join(get_config().get('logs', 'dir'), log_file))
            file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))
            file_handler.setLevel(logging.DEBUG)
            _leapp_logger.addHandler(file_handler)

        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                if is_debug():
                    handler.setLevel(logging.DEBUG)
                elif is_verbose():
                    handler.setLevel(logging.INFO)
                else:
                    handler.setLevel(logging.ERROR)

        _leapp_logger.info('Logging has been initialized')

    return _leapp_logger
