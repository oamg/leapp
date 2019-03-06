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
from leapp.libraries.stdlib import api
from leapp.libraries.stdlib.call import _call, STDOUT


class CalledProcessError(LeappError):
    """
    Leapp Call Process Exception Error.

    Raised when the result of a called process is of a none zero return code.
    """
    def __init__(self, message, command, result):
        """
        Initialize CalledProcessError Exception.
        :param message: An CalledProcessError exception message.
        :param command: The command that has been executed, with its arguments.
        :param result: A non-zero whatever result that the command returned.
        """
        super(CalledProcessError, self).__init__(message)
        self._result = result
        self.command = command

    @property
    def stdout(self):
        """
        Retrieve the stdout.
        :return: Standard Output.
        """
        return self._result.get('stdout')

    @property
    def stderr(self):
        """
        Retrieve the stderr.
        :return: Standard Error.
        """
        return self._result.get('stderr')

    @property
    def exit_code(self):
        """
        Retrieve the exit code.
        :return: An exit code.
        """
        return self._result.get('exit_code')

    @property
    def signal(self):
        """
        Retrieve the signal which the process was signalled by.
        :return: A signal that the process received.
        """
        return self._result.get('signal')

    @property
    def pid(self):
        """
        Retrieve the pid of the finished process.
        :return: The pid of the process.
        """
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
    """
    Log into either STDOUT or to STDERR.

    Buffer Output Discrimination is based on fd_type in fd_info while in a leapp debug mode.

    :param fd_info: Contains File descriptor type
    :type fd_info: tuple
    :param buffer: buffer interface
    :type buffer: bytes array
    """
    (_unused, fd_type) = fd_info
    if os.getenv('LEAPP_VERBOSE', '0') == '1':
        if fd_type == STDOUT:
            sys.stdout.write(buffer)
        else:
            sys.stderr.write(buffer)


def run(args, split=False, callback_raw=_logging_handler):
    """
    Run a command and return its result as a dict.

    The execution of the program and it's results are captured by the audit.

    :param args: Command to execute
    :type args: list or tuple
    :param split: Split the output on newlines
    :type split: bool
    :param callback_raw: Optional custom callback executed on raw data to print in console
    :type callback_raw: (fd: int, buffer: bytes) -> None
    :return: {'stdout' : stdout, 'stderr': stderr, 'signal': signal, 'exit_code': exit_code, 'pid': pid}
    :rtype: dict
    """
    _id = str(uuid.uuid4())
    result = None
    try:
        create_audit_entry('process-start', {'id': _id, 'parameters': args})
        result = _call(args, callback_raw=callback_raw)
        if result['exit_code'] != 0:
            raise CalledProcessError(
                message="A Leapp Command Error occurred. ",
                command=args,
                result=result
            )
        else:
            if split:
                result.update({
                    'stdout': result['stdout'].splitlines()
                })
    finally:
        create_audit_entry('process-end', _id)
        create_audit_entry('process-result', {'id': _id, 'parameters': args, 'result': result})
    return result
