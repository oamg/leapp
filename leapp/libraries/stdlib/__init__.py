"""
:py:mod:`leapp.libraries.stdlib`
represents a location for functions that otherwise would be defined multiple times across leapp actors
and at the same time, they are really useful for other actors.
"""
import os
import sys

import subprocess
import uuid

import six

from leapp.exceptions import CommandError
from leapp.utils.audit import create_audit_entry
from leapp.libraries.stdlib import call, api


def call(args, split=True):
    """
    Call an external program, capture and automatically utf-8 decode its output.
    Then, suppress output to stderr and redirect to /dev/null.

    :param args: Command to execute
    :type args: list
    :param split: Split the output on newlines
    :type split: bool
    :return: stdout output, 'utf-8' decoded, split by lines if split=True
    :rtype: unicode/str or [unicode/str] if split=True
    """

    r = None
    with open(os.devnull, mode='w') as err:
        if six.PY3:
            r = subprocess.check_output(args, stderr=err, encoding='utf-8')
        else:
            r = subprocess.check_output(args, stderr=err).decode('utf-8')
    if split:
        return r.splitlines()
    return r


def _logging_handler((fd, fd_type), buffer):
    if os.getenv('LEAPP_DEBUG', '0') == '1':
        if fd_type == call.STDOUT:
            sys.stdout.write(buffer)
        else:
            sys.stderr.write(buffer)


def new_call(args):
    """
    Call the Leapp's stdlib _call

    :param args: Command to execute
    :return: stdout output, 'utf-8' decoded
    """
    _id = str(uuid.uuid4())
    result_data = None
    try:
        create_audit_entry('process-start', {'id': _id, 'parameters': args})
        result_data = call._call(args, callback_raw=_logging_handler)
    finally:
        create_audit_entry('process-end', _id)
        create_audit_entry('process-result', {'id': _id, 'parameters': args, 'result': result_data})
    return result_data


def new_checked_call(args, split=False):
    """
    Call the audited call and check result, split the result into multiple lines if requested

    :param args: Command to execute
    :param split: Split the output on newlines
    :return: stdout output, 'utf-8' decoded, split by lines if split=True
    """
    result = new_call(args)
    if result['exit_code'] != 0:
        failed_command = "Command: " + str(args[0])
        command_stdout = "Result stdout: " + result['stdout']
        error_message = " stderr: " + result['stderr']
        raise CommandError(
            message="A Leapp Command Error occurred. " + failed_command + command_stdout + error_message
        )
    else:
        if split:
            return result['stdout'].splitlines()
        return result['stdout']
