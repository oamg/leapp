from __future__ import print_function

import hashlib
import json
import os
import sys
from contextlib import contextmanager

from leapp.exceptions import LeappRuntimeError
from leapp.models import ErrorModel
from leapp.utils.audit import get_audit_entry


def _is_verbose():
    """Redefinition of is_verbose from leapp.libraries.stdlib.config because it leads to import errors"""
    return os.getenv('LEAPP_VERBOSE', '0') == '1'


class Color(object):
    reset = "\033[0m" if sys.stdout.isatty() else ""
    bold = "\033[1m" if sys.stdout.isatty() else ""
    red = "\033[1;31m" if sys.stdout.isatty() else ""
    green = "\033[1;32m" if sys.stdout.isatty() else ""
    yellow = "\033[1;33m" if sys.stdout.isatty() else ""


def pretty_block_text(string, color=Color.bold, width=60):
    return "\n{color}{separator}\n{text}\n{separator}{reset}\n".format(
        color=color,
        separator="=" * width,
        reset=Color.reset,
        text=string.center(width))


@contextmanager
def pretty_block(text, target, end_text=None, color=Color.bold, width=60):
    target.write(pretty_block_text(text, color=color, width=width))
    target.write('\n')
    yield
    target.write(pretty_block_text(end_text or 'END OF {}'.format(text), color=color, width=width))
    target.write('\n')


def print_error(error):
    model = ErrorModel.create(json.loads(error['message']['data']))
    sys.stdout.write("{red}{time} [{severity}]{reset} Actor: {actor}\nMessage: {message}\n".format(
        red=Color.red, reset=Color.reset, severity=model.severity.upper(),
        message=model.message, time=model.time, actor=model.actor))
    if model.details:
        print('Summary:')
        details = json.loads(model.details)
        for detail in details:
            print('    {k}: {v}'.format(
                k=detail.capitalize(),
                v=details[detail].rstrip().replace('\n', '\n' + ' ' * (6 + len(detail)))))


def report_inhibitors(context_id):
    # The following imports are required to be here to avoid import loop problems
    from leapp.reporting import Groups  # pylint: disable=import-outside-toplevel
    from leapp.utils.report import fetch_upgrade_report_messages  # pylint: disable=import-outside-toplevel
    reports = fetch_upgrade_report_messages(context_id)
    inhibitors = [report for report in reports if Groups.INHIBITOR in report.get('groups', [])]
    if inhibitors:
        text = 'UPGRADE INHIBITED'
        with pretty_block(text=text, end_text=text, color=Color.red, target=sys.stdout):
            print('Upgrade has been inhibited due to the following problems:')
            for position, report in enumerate(inhibitors, start=1):
                print('{idx:5}. Inhibitor: {title}'.format(idx=position, title=report['title']))
            print('Consult the pre-upgrade report for details and possible remediation.')


def report_deprecations(context_id, start=None):
    deprecations = get_audit_entry(event='deprecation', context=context_id)
    if start:
        start_stamp = start.isoformat() + 'Z'
        deprecations = [d for d in deprecations if d['stamp'] > start_stamp]
    if deprecations:
        cache = set()
        with pretty_block("USE OF DEPRECATED ENTITIES", target=sys.stderr, color=Color.red):
            for deprecation in deprecations:
                entry_data = json.loads(deprecation['data'])
                # Deduplicate messages
                key = hashlib.sha256(json.dumps(entry_data, sort_keys=True)).hexdigest()
                if key in cache:
                    continue
                # Add current message to the cache
                cache.add(key)
                # Print the message
                sys.stderr.write(
                    '{message} @ {filename}:{lineno}\nNear: {line}\nReason: {reason}\n{separator}\n'.format(
                        separator='-' * 60, **entry_data)
                )


def report_errors(errors):
    if errors:
        with pretty_block("ERRORS", target=sys.stdout, color=Color.red):
            for error in errors:
                print_error(error)


def report_info(report_paths, log_paths, answerfile=None, fail=False):
    report_paths = [report_paths] if not isinstance(report_paths, list) else report_paths
    log_paths = [log_paths] if not isinstance(report_paths, list) else log_paths

    if log_paths:
        sys.stdout.write("\n")
        for log_path in log_paths:
            sys.stdout.write("Debug output written to {path}\n".format(path=log_path))

    if report_paths:
        with pretty_block("REPORT", target=sys.stdout, color=Color.bold if fail else Color.green):
            for report_path in report_paths:
                sys.stdout.write("A report has been generated at {path}\n".format(path=report_path))

    if answerfile:
        sys.stdout.write("Answerfile has been generated at {}\n".format(answerfile))


def report_unsupported(devel_vars, experimental):
    text = "UNSUPPORTED UPGRADE"
    with pretty_block(text=text, end_text=text, target=sys.stdout, color=Color.yellow):
        sys.stdout.write("Variable LEAPP_UNSUPPORTED has been detected. Proceeding at your own risk.\n")

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


@contextmanager
def beautify_actor_exception():
    try:
        try:
            yield
        except LeappRuntimeError as e:
            msg = '{} - Please check the above details'.format(e.message)
            sys.stderr.write("\n")
            sys.stderr.write(pretty_block_text(msg, color="", width=len(msg)))
    finally:
        pass


def display_status_current_phase(phase):
    if not _is_verbose():
        print('==> Processing phase `{name}`'.format(name=phase[0].name))


def _get_description_title(actor):
    lines = actor.description.strip().split('\n')
    return lines[0].strip() if lines else actor.name


def display_status_current_actor(actor, designation=''):
    if not _is_verbose():
        print('====> * {actor}{designation}\n        {title}'.format(actor=actor.name,
                                                                     title=_get_description_title(actor),
                                                                     designation=designation))
