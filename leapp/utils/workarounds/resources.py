import resource
from leapp.exceptions import FrameworkInitializationError


def apply_workaround():
    """
    Set resource limits for the maximum number of open file descriptors and the maximum writable file size.

    :raises: `CommandError` if the resource limits cannot be set
    """

    def set_resource_limit(resource_type, soft, hard):
        rtype_string = (
            'open file descriptors' if resource_type == resource.RLIMIT_NOFILE
            else 'writable file size' if resource_type == resource.RLIMIT_FSIZE
            else 'unknown resource'
        )
        try:
            resource.setrlimit(resource_type, (soft, hard))
        except ValueError as err:
            raise FrameworkInitializationError(
                'Unable to set the required soft limit of resource due to system restrictions. '
                'This limit is necessary to prevent the program from crashin. '
                'Resource type: {}, error: {}'.format(rtype_string, err)
            )
        except OSError as err:
            raise FrameworkInitializationError(
                'Failed to set resource limit. Resource type: {}, error: {}'.format(rtype_string, err)
            )

    soft_nofile, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    soft_fsize, _ = resource.getrlimit(resource.RLIMIT_FSIZE)
    nofile_limit = 1024 * 16
    fsize_limit = resource.RLIM_INFINITY

    if soft_nofile < nofile_limit:
        set_resource_limit(resource.RLIMIT_NOFILE, nofile_limit, nofile_limit)

    if soft_fsize != fsize_limit:
        set_resource_limit(resource.RLIMIT_FSIZE, fsize_limit, fsize_limit)
