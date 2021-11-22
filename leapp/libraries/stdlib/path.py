import os


def get_file_path(directories, name):
    """
    Finds the first matching file path within directories.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    for path in directories:
        path = os.path.join(path, name)
        if os.path.isfile(path):
            return path


def get_folder_path(directories, name):
    """
    Finds the first matching folder path within directories.

    :param name: Name of the folder
    :type name: str
    :return: Found folder path
    :rtype: str or None
    """
    for path in directories:
        path = os.path.join(path, name)
        if os.path.isdir(path):
            return path


def get_tool_path(directories, name):
    """
    Finds the first matching executable file within directories.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    for path in directories:
        path = os.path.join(path, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path


# NOTE(ivasilev) You can use the functions below standalone with
# repository = load_repositories_from('repo_path', '/etc/leapp/repo.d/', manager=None)
def get_common_file_path(repository, name):
    return get_file_path(repository.files, name)


def get_common_folder_path(repository, name):
    return get_folder_path(repository.files, name)


def get_common_tool_path(repository, name):
    return get_tool_path(repository.files, name)
