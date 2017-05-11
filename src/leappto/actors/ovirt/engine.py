import leappto.actors.meta as meta
from leappto.actors import Actor
from leappto.actors.apache import Apache


@meta.services('ovirt-engine')
@meta.rpms('ovirt-engine', 'ovirt-engine-webadmin-portal')
@meta.targets_services('ovirt-engine')
@meta.addr_link('localhost:8702', Apache)
class Engine(Actor):
    def __init__(self, *args, **kwargs):
        super(Engine, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    from pprint import pprint
    pprint(Engine.leapp_meta())
