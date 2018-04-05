class ContainerOS(object):
    """
    Baseclass defining OS for templating system
    """

    IMAGE_ROOT = "leapp"
    IMAGE_BASENAME = "leapp-scratch"
    IMAGE_TAG = "latest"

    def is_systemd(self):
        """
        tells if the system is using systemd

        :returns: true, if OS is using systemd
        :rtype: bool
        """
        raise NotImplemented()

    def base_image(self):
        """
        :returns: the name of base docker image
        :rtype: string
        """
        raise NotImplemented()


class UpstartContainerOS(ContainerOS):
    """
    Baseclass for upstart based OS
    """

    IMAGE_TAG = "6"

    def is_systemd(self):
        return False

    def base_image(self):
        return "{}/{}:{}".format(self.IMAGE_ROOT, self.IMAGE_BASENAME, self.IMAGE_TAG)


class SystemdContainerOS(ContainerOS):
    """
    Baseclass for systemd based OS
    """

    IMAGE_TAG = "7"

    def is_systemd(self):
        return True

    def base_image(self):
        return "{}/{}:{}".format(self.IMAGE_ROOT, self.IMAGE_BASENAME, self.IMAGE_TAG)


class RHEL6ContainerOS(UpstartContainerOS):
    """
    RHEL6/CentOS 6 OS definitions
    """

    IMAGE_TAG = "6"


class RHEL7ContainerOS(SystemdContainerOS):
    """
    RHEL7/CentOS 7 OS definitions
    """

    IMAGE_TAG = "7"
