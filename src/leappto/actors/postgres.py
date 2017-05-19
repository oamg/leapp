import leappto.actors.meta as meta
from leappto.actors import Actor


@meta.ports(5432)
@meta.config_files('/etc/httpd/co')
@meta.services('postgresql')
@meta.rpms('postgresql-server')
@meta.targets_services('postgresql')
# @meta.directory('/var/run/postgresql', user='postgres', group='postgres', mode='0755')
class Postgres(Actor):
    def __init__(self, *args, **kwargs):
        super(Postgres, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    from pprint import pprint
    pprint(Postgres.leapp_meta())
