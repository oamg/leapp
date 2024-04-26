from __future__ import print_function

import hashlib
import json
import os
import sys
from contextlib import contextmanager
import six

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


def _print_errors_summary(errors):
    width = 4 + len(str(len(errors)))
    for position, error in enumerate(errors, start=1):
        model = ErrorModel.create(json.loads(error['message']['data']))

        error_message = model.message
        if six.PY2:
            error_message = model.message.encode('utf-8', 'xmlcharrefreplace')

        sys.stdout.write("{idx:{width}}. Actor: {actor}\n{spacer}  Message: {message}\n".format(
            idx=position, width=width, spacer=" " * width, message=error_message, actor=model.actor))


def print_error(error):
    model = ErrorModel.create(json.loads(error['message']['data']))

    error_message = model.message
    if six.PY2:
        error_message = model.message.encode('utf-8', 'xmlcharrefreplace')

    sys.stdout.write("{red}{time} [{severity}]{reset} Actor: {actor}\nMessage: {message}\n".format(
        red=Color.red, reset=Color.reset, severity=model.severity.upper(),
        message=error_message, time=model.time, actor=model.actor))
    if model.details:
        print('Summary:')
        details = json.loads(model.details)
        for detail in details:
            print('    {k}: {v}'.format(
                k=detail.capitalize(),
                v=details[detail].rstrip().replace('\n', '\n' + ' ' * (6 + len(detail)))))


def _print_report_titles(reports):
    width = 4 + len(str(len(reports)))
    for position, report in enumerate(reports, start=1):
        print('{idx:{width}}. {title}'.format(idx=position, width=width, title=report['title']))


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


def _filter_reports(reports, severity=None, has_flag=None):
    # The following imports are required to be here to avoid import loop problems
    from leapp.reporting import Groups # noqa; pylint: disable=import-outside-toplevel
    from leapp.utils.report import has_flag_group # noqa; pylint: disable=import-outside-toplevel

    def is_ordinary_report(report):
        return not has_flag_group(report, Groups._ERROR) and not has_flag_group(report, Groups.INHIBITOR)

    result = reports
    if has_flag is False:
        result = [rep for rep in result if is_ordinary_report(rep)]
    elif has_flag is not None:
        result = [rep for rep in result if has_flag_group(rep, has_flag)]
    if severity:
        result = [rep for rep in result if rep['severity'] == severity]

    return result


def _print_reports_summary(reports):
    # The following imports are required to be here to avoid import loop problems
    from leapp.reporting import Groups, Severity # noqa; pylint: disable=import-outside-toplevel

    errors = _filter_reports(reports, has_flag=Groups._ERROR)
    inhibitors = _filter_reports(reports, has_flag=Groups.INHIBITOR)

    ordinary = _filter_reports(reports, has_flag=False)

    high = _filter_reports(ordinary, Severity.HIGH)
    medium = _filter_reports(ordinary, Severity.MEDIUM)
    low = _filter_reports(ordinary, Severity.LOW)
    info = _filter_reports(ordinary, Severity.INFO)

    print('Reports summary:')
    print('    Errors:                  {:5}'.format(len(errors)))
    print('    Inhibitors:              {:5}'.format(len(inhibitors)))
    print('    HIGH severity reports:   {:5}'.format(len(high)))
    print('    MEDIUM severity reports: {:5}'.format(len(medium)))
    print('    LOW severity reports:    {:5}'.format(len(low)))
    print('    INFO severity reports:   {:5}'.format(len(info)))


# NOTE(mmatuska): it would be nicer to get the errors from reports,
# however the reports don't have the information about which actor raised the error :(
def report_info(context_id, report_paths, log_paths, answerfile=None, fail=False, errors=None):
    report_paths = [report_paths] if not isinstance(report_paths, list) else report_paths
    log_paths = [log_paths] if not isinstance(log_paths, list) else log_paths

    if log_paths:
        if not errors:  # there is already a newline after the errors section
            sys.stdout.write("\n")
        for log_path in log_paths:
            sys.stdout.write("Debug output written to {path}\n".format(path=log_path))

    if report_paths:
        # The following imports are required to be here to avoid import loop problems
        from leapp.reporting import Severity  # noqa; pylint: disable=import-outside-toplevel
        from leapp.utils.report import fetch_upgrade_report_messages, Groups # noqa; pylint: disable=import-outside-toplevel

        reports = fetch_upgrade_report_messages(context_id)

        inhibitors = _filter_reports(reports, has_flag=Groups.INHIBITOR)

        ordinary = _filter_reports(reports, has_flag=False)
        high = _filter_reports(ordinary, Severity.HIGH)
        medium = _filter_reports(ordinary, Severity.MEDIUM)

        color = Color.green
        if medium or high:
            color = Color.yellow
        if fail:
            color = Color.red

        with pretty_block("REPORT OVERVIEW", target=sys.stdout, color=color):
            if errors:
                print('Following errors occurred and the upgrade cannot continue:')
                _print_errors_summary(errors)
                sys.stdout.write('\n')

            if inhibitors:
                print('Upgrade has been inhibited due to the following problems:')
                _print_report_titles(inhibitors)
                sys.stdout.write('\n')

            if high or medium:
                print('HIGH and MEDIUM severity reports:')
                _print_report_titles(high + medium)
                sys.stdout.write('\n')

            _print_reports_summary(reports)

            print(
                '\n{bold}Before continuing, review the full report below for details'
                ' about discovered problems and possible remediation instructions:{reset}'
                .format(bold=Color.bold, reset=Color.reset)
            )
            for report_path in sorted(report_paths, reverse=True):
                # NOTE: sort hack -> print .txt first
                sys.stdout.write("    A report has been generated at {path}\n".format(path=report_path))

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
