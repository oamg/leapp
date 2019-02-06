"""
:py:mod:`leapp.libraries.stdlib`
represents a location for functions that otherwise would be defined multiple times across leapp actors
and at the same time, they are really useful for other actors.
"""
import six
import subprocess
import os

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
