import leappto.actors.meta as meta
from leappto.actors import Actor

_PROXY_SETUP_CONF='/etc/ovirt-engine/ovirt-websocket-proxy.conf.d/10-setup.conf'

@meta.users('ovirt')
@meta.ports(6100)
@meta.config_files(_PROXY_SETUP_CONF)
@meta.services('ovirt-websocket-proxy')
@meta.rpms('ovirt-engine-websocket-proxy')
@meta.targets_services('ovirt-websocket-proxy')
class WSProxy(Actor):
    def __init__(self, *args, **kwargs):
        super(WSProxy, self).__init__(*args, **kwargs)
