"""
:py:mod:`leapp.libraries.stdlib`
represents a location for functions that otherwise would be defined multiple times across leapp actors
and at the same time, they are really useful for other actors.
"""
import os
import sys

import six
import subprocess
import uuid

from leapp.utils.audit import create_audit_entry
from leapp.libraries.stdlib import call


class CalledProcessError(Exception):
    pass

from leapp.libraries.stdlib import api


def call(args, split=True):
    """
    Call an external program, capture and automatically utf-8 decode its ouput.
    Then, supress output to stderr and redirect to /dev/null.

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


def _logging_handler(fd, buffer):
    if os.getenv('LEAPP_DEBUG', '0') == '1':
        if fd == call.STDOUT:
            sys.stdout.write(buffer)
        else:
            sys.stderr.write(buffer)


def new_call(args):
    """
    Call the Leapp's stdlib _call
    :param args:
    :return:
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
    Call the audited call and check result split the result into multiple lines if requested

    :param args:
    :param split:
    :return:
    """
    result = new_call(args)
    if result['exit_code'] != 0:
        raise CalledProcessError("A Leapp CalledProcessError occurred." + "Command: " + str(args[0]))
    else:
        if split:
            return result['stdout'].splitlines()
        return result['stdout']
