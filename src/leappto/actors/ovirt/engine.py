import leappto.actors.meta as meta
from leappto.actors import Actor
from leappto.actors.apache import Apache
from leappto.actors.postgres import Postgres

@meta.force_host_networking_to(Apache)
# Forces host networking instead of this: where this should replace the IP
# with the connection details for the engine container
#@meta.addr_link('127.0.0.1:8702', Apache,
#        ('proxy_config', '/etc/httpd/conf.d/z-ovirt-engine-proxy.conf'))
@meta.requires_host_networking
@meta.users('ovirt')
@meta.services('ovirt-engine')
@meta.rpms('ovirt-engine', 'ovirt-engine-webadmin-portal')
@meta.targets_services('ovirt-engine')
@meta.require_link(Postgres)
class Engine(Actor):
    def __init__(self, *args, **kwargs):
        super(Engine, self).__init__(*args, **kwargs)

    def fixup(self):
        self.driver.exec_command(
                "sed -i 's/localhost/container-postgresql/g " + \
                "/opt/leapp-to/container/etc/ovirt-engine/engine.conf.d/10-setup-database.conf'")

if __name__ == '__main__':
    from pprint import pprint
    pprint(Engine.leapp_meta())
