import os
import multiprocessing.util


def apply_workaround():
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

        def __call__(self, *args, **kwargs):    # pylint: disable=signature-differs
            if self._pid != os.getpid():
                return None
            return super(FixedFinalize, self).__call__(*args, **kwargs)

    setattr(multiprocessing.util, 'Finalize', FixedFinalize)
