import os


def _get_path_size(path):
    """
    Get path size in bytes.

    :param path: path which size will be calculated
    :type path: string

    :return: size of given path
    :rtype: long int

    :raises ValueError: if given path is not a dir
    """
    size = 0L
    if not os.path.isdir(path):
        raise ValueError('Path is not a dir: {}'.format(path))
    for root, dirs, files in os.walk(path):
        for fname in files:
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath):
                size += os.path.getsize(fpath)
    return size
