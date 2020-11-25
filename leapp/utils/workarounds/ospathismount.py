import os

_MOUNTS_PATH = '/proc/self/mounts'


def _ismount_with_bindmounts(path):
    if not os.path.exists(path):
        print("Path {path} does not exist".format(path=path))
        return False
    if os.path.islink(path):
        print("Path {path} is link".format(path=path))
        return False
    with open(_MOUNTS_PATH) as f:
        for line in f:
            try:
                target = line.split(' ')[1]
            except IndexError:
                continue
            if target == path:
                return True
    print("Mount for {path} not found - Not mounted".format(path=path))
    return False


def apply_workaround():
    os.path.ismount = _ismount_with_bindmounts
