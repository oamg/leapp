from __future__ import print_function
from multiprocessing import util, Process, Manager

import os
import pytest

import leapp  # noqa: F401; pylint: disable=unused-import
from leapp.utils.workarounds import fqdn


def test_mp_is_patched():

    def child_fun(_lst):
        pid = os.fork()
        if not pid:
            os.execvpe('whatever', [], os.environ)
        else:
            os.wait()

    m = Manager()
    lst = m.list()

    p = Process(target=child_fun, args=(lst,))
    p.start()
    p.join()
    if lst:
        for el in lst:
            print(el)


def test_mp_workaround_applied():
    if getattr(util, 'os', None) is None:
        assert util.Finalize.__name__ == 'FixedFinalize'


@pytest.mark.parametrize(
    ('input_fqdn', 'valid'),
    [
        ('foo.bar.com', True),
        ('foo\xa0bar.foo.com', False),
        ('-foo.bar', False),
        ('foo.bar-', False),
        ('foo.-bar.1234', False),
        ('a1.b2.c3', True),
        ('123.foo.bar', True),
        ('123.f-o-o.b-a-r', True),
    ]
)
def test_fqdn_is_patched(input_fqdn, valid):

    def getfqdn():
        return input_fqdn

    fn = fqdn.decorate_getfqdn(getfqdn)
    expected_fqdn = input_fqdn if valid else 'invalid.hostname'
    assert fn() == expected_fqdn
