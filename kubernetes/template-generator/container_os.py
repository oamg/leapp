"""
    Baseclass defining OS for templating system
"""
class ContainerOS(object):
    """
        tells if the system is using systemd

        @return Boolean     true, if OS is using systemd
    """
    def is_systemd(self):
        raise NotImplemented()

    """
        returns the name of base docker image

        @return string
    """
    def base_image(self):
        raise NotImplemented()

"""
    Baseclass for upstart based OS
"""
class UpstartContainerOS(ContainerOS):
    def is_systemd(self):
        return False

    def base_image(self):
        return "gazdown/leapp-scratch"


"""
    Baseclass for systemd based OS
"""
class SystemDContainerOS(ContainerOS):
    def is_systemd(self):
        return True

    def base_image(self):
        return "gazdown/leapp-scratch"

"""
    RHEL6/CentOS 6 OS definitions
"""
class RHEL6ContainerOS(UpstartContainerOS):
    def base_image(self):
        return "gazdown/leapp-scratch:6"

"""
    RHEL7/CentOS 7 OS definitions
"""
class RHEL7ContainerOS(SystemDContainerOS):
    def base_image(self):
        return "gazdown/leapp-scratch:7"
