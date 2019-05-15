import json
import sys
from pprint import pformat
from contextlib import contextmanager

from leapp.models import ErrorModel
from leapp.exceptions import LeappRuntimeError


def _get_colors():
    if sys.stdout.isatty():
        return "\033[1;31m", "\033[0;0m"
    return "", ""


def report_errors(errors):
    if errors:
        red, reset = _get_colors()
        sys.stdout.write("""{red}
============================================================
                        ERRORS
============================================================{reset}\n\n""".format(red=red, reset=reset))
        for error in errors:
            print_error(error)
        sys.stdout.write("""{red}
============================================================
                     END OF ERRORS
============================================================{reset}\n\n""".format(red=red, reset=reset))


def print_error(error):
    model = ErrorModel.create(json.loads(error['message']['data']))
    red, reset = _get_colors()
    sys.stdout.write("{red}{time} [{severity}]{reset} Actor: {actor} Message: {message}\n".format(
        red=red, reset=reset, severity=model.severity.upper(), message=model.message, time=model.time,
        actor=model.actor))
    if model.details:
        print('Detail: ' + pformat(json.loads(model.details)))


@contextmanager
def beautify_actor_exception():
    try:
        try:
            yield
        except LeappRuntimeError as e:
            msg = '{} - Please check the above details'.format(e.message)
            sys.stderr.write('\n')
            sys.stderr.write('=' * len(msg) + '\n')
            sys.stderr.write(msg + '\n')
            sys.stderr.write('=' * len(msg) + '\n')
            sys.stderr.write('\n')
    finally:
        pass
