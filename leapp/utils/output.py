from __future__ import print_function
import json
import sys
from pprint import pformat
from contextlib import contextmanager

from leapp.models import ErrorModel
from leapp.exceptions import LeappRuntimeError


class Color(object):
    reset = "\033[0m" if sys.stdout.isatty() else ""
    bold = "\033[1m" if sys.stdout.isatty() else ""
    red = "\033[1;31m" if sys.stdout.isatty() else ""
    green = "\033[1;32m" if sys.stdout.isatty() else ""
    yellow = "\033[1;33m" if sys.stdout.isatty() else ""


def pretty_block(string, color=Color.bold, width=60):
    return "\n{color}{separator}\n{text}\n{separator}{reset}\n".format(
        color=color,
        separator="=" * width,
        reset=Color.reset,
        text=string.center(width))


def print_error(error):
    model = ErrorModel.create(json.loads(error['message']['data']))
    sys.stdout.write("{red}{time} [{severity}]{reset} Actor: {actor} Message: {message}\n".format(
        red=Color.red, reset=Color.reset, severity=model.severity.upper(),
        message=model.message, time=model.time, actor=model.actor))
    if model.details:
        print('Detail: ' + pformat(json.loads(model.details)))


def report_errors(errors):
    if errors:
        sys.stdout.write(pretty_block("ERRORS", color=Color.red))
        sys.stdout.write("\n")
        for error in errors:
            print_error(error)
        sys.stdout.write(pretty_block("END OF ERRORS", color=Color.red))


def report_info(path, fail=False):
    paths = [path] if not isinstance(path, list) else path
    if paths:
        sys.stdout.write(pretty_block("REPORT", color=Color.bold if fail else Color.green))
        sys.stdout.write("\n")
        for report_path in paths:
            sys.stdout.write("A report has been generated at {path}\n".format(path=report_path))
        sys.stdout.write(pretty_block("END OF REPORT", color=Color.bold if fail else Color.green))


def report_unsupported(devel_vars, experimental):
    sys.stdout.write(pretty_block("UNSUPPORTED UPGRADE", color=Color.yellow))
    sys.stdout.write("\nVariable LEAPP_UNSUPPORTED has been detected. Proceeding at your own risk.\n")

    if devel_vars:
        sys.stdout.write("{yellow}Development variables{reset} have been detected:\n".format(
            yellow=Color.yellow, reset=Color.reset))
        for key in devel_vars:
            sys.stdout.write("- {key}={value}\n".format(key=key, value=devel_vars[key]))
    if experimental:
        sys.stdout.write("{yellow}Experimental actors{reset} have been detected:\n".format(
            yellow=Color.yellow, reset=Color.reset))
        for actor in experimental:
            sys.stdout.write("- {actor}\n".format(actor=actor))
    sys.stdout.write(pretty_block("UNSUPPORTED UPGRADE", color=Color.yellow))
    sys.stdout.write("\n")


@contextmanager
def beautify_actor_exception():
    try:
        try:
            yield
        except LeappRuntimeError as e:
            msg = '{} - Please check the above details'.format(e.message)
            sys.stderr.write("\n")
            sys.stderr.write(pretty_block(msg, color="", width=len(msg)))
    finally:
        pass
