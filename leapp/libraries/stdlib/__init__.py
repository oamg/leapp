"""
:py:mod:`leapp.libraries.stdlib`
represents a location for functions that otherwise would be defined multiple times across leapp actors
and at the same time, they are really useful for other actors.
"""
import logging
import os
import sys
import uuid
import base64

from leapp.exceptions import LeappError
from leapp.utils.audit import create_audit_entry
from leapp.libraries.stdlib import api
from leapp.libraries.stdlib.call import _call, STDOUT
from leapp.libraries.stdlib.config import is_debug


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


# FIXME: Issue #488
def __write_raw(fd_info, a_buffer):
    """
    Raw write to fd compatible in Py2 and Py3 (3.3+)

    Buffer Output Discrimination is based on fd_type in fd_info.

    :param fd_info: Contains File descriptor type
    :type fd_info: tuple
    :param a_buffer: buffer interface
    :type a_buffer: bytes array
    """
    (unused_fd, fd_type) = fd_info
    if sys.version_info > (3, 0):
        if fd_type == STDOUT:
            fd = sys.stdout.fileno()
        else:
            # FIXME: Issue #488 - what to do in case fd_type != STDERR?
            fd = sys.stderr.fileno()
        os.writev(fd, [a_buffer])
    else:
        if fd_type == STDOUT:
            sys.stdout.write(a_buffer)
        else:
            sys.stderr.write(a_buffer)


# FIXME: Issue #488
def _console_logging_handler(fd_info, a_buffer):
    """
    Log into either STDOUT or to STDERR.

    Buffer Output Discrimination is based on fd_type in fd_info while in a leapp debug mode.

    :param fd_info: Contains File descriptor type
    :type fd_info: tuple
    :param a_buffer: buffer interface
    :type a_buffer: bytes array
    """
    if is_debug():
        __write_raw(fd_info, a_buffer)


def _logfile_logging_handler(fd_info, line):  # pylint: disable=unused-argument
    """
    Log into logfile

    :param fd_info: Contains File descriptor type (not used)
    :type fd_info: tuple
    :param line: data to be printed to a logfile
    :type line: string
    """
    def _raise_level(handlers):
        for handler in handlers:
            handler.setLevel(handler.level + 1)

    def _restore_level(handlers, levels):
        for handler, level in zip(handlers, levels):
            handler.setLevel(level)

    if is_debug():
        # raise logging level of stream handlers above DEBUG to avoid duplicated output to stdout/stderr
        logger_handlers = api.current_logger().root.handlers
        stream_handlers = [handler for handler in logger_handlers if isinstance(handler, logging.StreamHandler)]
        handler_levels = [handler.level for handler in stream_handlers]
        _raise_level(stream_handlers)
        api.current_logger().debug(line)
        _restore_level(stream_handlers, handler_levels)
    else:
        api.current_logger().debug(line)


def run(args, split=False, callback_raw=_console_logging_handler, callback_linebuffered=_logfile_logging_handler,
        env=None, checked=True, stdin=None, encoding='utf-8'):
    """
    Run a command and return its result as a dict.

    The execution of the program and it's results are captured by the audit.

    :param args: Command to execute
    :type args: list or tuple
    :param split: Split the output on newlines
    :type split: bool
    :param callback_raw: Optional custom callback executed on raw data to print in console
    :type callback_raw: (fd: int, buffer: bytes) -> None
    :param env: Environment variables to use for execution of the command
    :type env: dict
    :param checked: Raise an exception on a non-zero exit code, default True
    :type checked: bool
    :param stdin: String or a file descriptor that will be written to stdin of the child process
    :type stdin: int, str
    :return: {'stdout' : stdout, 'stderr': stderr, 'signal': signal, 'exit_code': exit_code, 'pid': pid}
    :rtype: dict
    """
    if not args:
        message = 'Command to call is missing.'
        api.current_logger().error(message)
        raise ValueError(message)
    api.current_logger().debug('External command has started: {0}'.format(str(args)))
    _id = str(uuid.uuid4())
    result = None
    try:
        create_audit_entry('process-start', {'id': _id, 'parameters': args, 'env': env})
        result = _call(args, callback_raw=callback_raw, callback_linebuffered=callback_linebuffered,
                       stdin=stdin, env=env, encoding=encoding)
        if checked and result['exit_code'] != 0:
            message = 'Command {0} failed with exit code {1}.'.format(str(args), result.get('exit_code'))
            api.current_logger().debug(message)
            raise CalledProcessError(
                message=message,
                command=args,
                result=result
            )
        if split and encoding:
            result.update({
                'stdout': result['stdout'].splitlines()
            })
    finally:
        if not encoding:
            audit_result = result.copy()
            audit_result.update({
                'stdout': 'Base64: ' + base64.b64encode(result['stdout']).decode('utf-8'),
                'stderr': 'Base64: ' + base64.b64encode(result['stderr']).decode('utf-8')
            })
        create_audit_entry('process-result', {'id': _id, 'parameters': args, 'result': result, 'env': env})
        api.current_logger().debug('External command has finished: {0}'.format(str(args)))
    return result
