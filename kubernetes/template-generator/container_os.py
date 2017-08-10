class ContainerOS(object):
    """
        Baseclass defining OS for templating system
    """

    def is_systemd(self):
        """
            tells if the system is using systemd

            @return Boolean     true, if OS is using systemd
        """
        raise NotImplemented()

    def base_image(self):
        """
            returns the name of base docker image

            @return string
        """
        raise NotImplemented()


class UpstartContainerOS(ContainerOS):
    """
        Baseclass for upstart based OS
    """
    def is_systemd(self):
        return False

    def base_image(self):
        return "gazdown/leapp-scratch"


class SystemDContainerOS(ContainerOS):
    """
        Baseclass for systemd based OS
    """
    def is_systemd(self):
        return True

    def base_image(self):
        return "gazdown/leapp-scratch"


class RHEL6ContainerOS(UpstartContainerOS):
    """
        RHEL6/CentOS 6 OS definitions
    """
    def base_image(self):
        return "gazdown/leapp-scratch:6"


class RHEL7ContainerOS(SystemDContainerOS):
    """
        RHEL7/CentOS 7 OS definitions
    """
    def base_image(self):
        return "gazdown/leapp-scratch:7"
