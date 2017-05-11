import leappto.actors.meta as meta
from leappto.actors import Actor


@meta.ports(80, 443, 8080, 8443)
@meta.config_files('/etc/httpd/conf/httpd.conf')
@meta.services('httpd')
@meta.rpms('httpd')
@meta.targets_services('httpd')
class Apache(Actor):
    def __init__(self, *args, **kwargs):
        super(Apache, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    from pprint import pprint
    pprint(Apache.leapp_meta())
