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

from leapp.exceptions import LeappError
from leapp.utils.audit import create_audit_entry
from leapp.libraries.stdlib import call, api


class CalledProcessError(LeappError):
    """ Leap Call Process Exception Error
    """
    def __init__(self, message, command, result):
        super(CalledProcessError, self).__init__(message)
        self._result = result
        self.command = command

    @property
    def stdout(self):
        return self._result.get('stdout')

    @property
    def stderr(self):
        return self._result.get('stderr')

    @property
    def exit_code(self):
        return self._result.get('exit_code')

    @property
    def signal(self):
        return self._result.get('signal')

    @property
    def pid(self):
        return self._result.get('pid')


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


def _logging_handler(fd_info, buffer):
    (_unused, fd_type) = fd_info
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
        raise CalledProcessError(
            message="A Leapp Command Error occurred. ",
            command=str(args[0]),
            result=result
        )
    else:
        if split:
            return result['stdout'].splitlines()
        return result['stdout']
