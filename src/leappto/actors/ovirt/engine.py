import leappto.actors.meta as meta
from leappto.actors import Actor
from leappto.actors.apache import Apache
from leappto.actors.postgres import Postgres

@meta.users('ovirt')
@meta.services('ovirt-engine')
@meta.rpms('ovirt-engine', 'ovirt-engine-webadmin-portal')
@meta.targets_services('ovirt-engine')
@meta.addr_link('127.0.0.1:8702', Apache,
        ('proxy_config', '/etc/httpd/conf.d/z-ovirt-engine-proxy.conf'))
@meta.require_link(Postgres)
class Engine(Actor):
    def __init__(self, *args, **kwargs):
        super(Engine, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    from pprint import pprint
    pprint(Engine.leapp_meta())
