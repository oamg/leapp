import leappto.actors.meta as meta
from leappto.actors import Actor

_PROXY_SETUP_CONF='/etc/ovirt-imageio-proxy/ovirt-imageio-proxy.conf'

@meta.users('ovirt')
@meta.ports(54323)
@meta.config_files(_PROXY_SETUP_CONF)
@meta.services('ovirt-imageio-proxy')
@meta.rpms('ovirt-imageio-proxy')
@meta.targets_services('ovirt-imageio-proxy')
class ImageIO(Actor):
    def __init__(self, *args, **kwargs):
        super(ImageIO, self).__init__(*args, **kwargs)
