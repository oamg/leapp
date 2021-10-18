import os
import multiprocessing.util
import multiprocessing

_start_method_set = False


def apply_workaround():
    global _start_method_set
    # Set start method for multiprocessing to fork (3.4+)
    set_start_method = getattr(multiprocessing, 'set_start_method', None)
    if not _start_method_set and set_start_method:
        set_start_method('fork')
        _start_method_set = True

    # Implements:
    # https://github.com/python/cpython/commit/e8a57b98ec8f2b161d4ad68ecc1433c9e3caad57
    #
    # Detection of fix: os imported to compare pids, before the fix os has not
    # been imported
    if getattr(multiprocessing.util, 'os', None):
        return

    class FixedFinalize(multiprocessing.util.Finalize):
        def __init__(self, *args, **kwargs):
            super(FixedFinalize, self).__init__(*args, **kwargs)
            self._pid = os.getpid()

        def __call__(self, *args, **kwargs):  # pylint: disable=signature-differs
            if self._pid != os.getpid():
                return None
            return super(FixedFinalize, self).__call__(*args, **kwargs)

    setattr(multiprocessing.util, 'Finalize', FixedFinalize)
