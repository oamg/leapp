import leapp.utils.workarounds.mp
import leapp.utils.workarounds.fqdn
import leapp.utils.workarounds.resources


def apply_workarounds():
    leapp.utils.workarounds.mp.apply_workaround()
    leapp.utils.workarounds.fqdn.apply_workaround()
    leapp.utils.workarounds.resources.apply_workaround()
