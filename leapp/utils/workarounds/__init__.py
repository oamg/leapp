import leapp.utils.workarounds.mp
import leapp.utils.workarounds.fqdn


def apply_workarounds():
    leapp.utils.workarounds.mp.apply_workaround()
    leapp.utils.workarounds.fqdn.apply_workaround()
