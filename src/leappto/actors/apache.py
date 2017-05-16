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

    def fixup(self):
        for entry in self.__class__.leapp_meta().get('fixup', []):
            t = entry[1]['arguments'][0]
            if t == 'proxy_config':
                f = entry[1]['arguments'][1]
                cname = 'container-' + entry[0].leapp_meta()['services'][0]
                self.driver.exec_command(
                        "sed -i 's/{0}/{1}/' {2} ".format(
                            entry[1]['address'],
                            entry[1]['address'].replace('127.0.0.1', cname),
                            '/opt/leapp-to/container' + entry[1]['arguments'][1])))

if __name__ == '__main__':
    from pprint import pprint
    pprint(Apache.leapp_meta())
