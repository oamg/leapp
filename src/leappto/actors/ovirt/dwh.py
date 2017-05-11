import leappto.actors.meta as meta
from leappto.actors import Actor

_DB_SETUP_CONF='/etc/ovirt-engine-dwh/ovirt-engine-dwhd.conf.d/10-setup-database.conf'

@meta.ports(54323)
@meta.config_files(_DB_SETUP_CONF)
@meta.services('ovirt-engine-dwhd')
@meta.rpms('ovirt-engine-dwh', 'ovirt-engine-dwh-setup')
@meta.targets_services('ovirt-engine-dwhd')
class DWH(Actor):
    def __init__(self, *args, **kwargs):
        super(DWH, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    from pprint import pprint
    pprint(DWH.leapp_meta())
