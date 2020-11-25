from __future__ import print_function
from multiprocessing import util, Process, Manager

import os

import leapp  # noqa: F401; pylint: disable=unused-import
import leapp.utils.workarounds.ospathismount


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


def test_os_path_ismount_workaround_applied():
    assert os.path.ismount == leapp.utils.workarounds.ospathismount._ismount_with_bindmounts


def test_os_path_ismount_detects_bindmounts(monkeypatch):
    bindmount_data_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mounts_fix')
    monkeypatch.setattr(
        leapp.utils.workarounds.ospathismount,
        '_MOUNTS_PATH',
        os.path.join(bindmount_data_root, 'mount_withoutbind')
    )
    assert not os.path.ismount('/usr')

    monkeypatch.setattr(
        leapp.utils.workarounds.ospathismount,
        '_MOUNTS_PATH',
        os.path.join(bindmount_data_root, 'mount_withbind')
    )
    assert os.path.ismount('/usr')
