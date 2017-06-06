"""LeApp CLI implementation"""

from argparse import ArgumentParser
from grp import getgrnam, getgrgid
from json import dumps, loads
from os import getuid, pipe, read, path
from tempfile import NamedTemporaryFile, mkdtemp
from pwd import getpwuid
from subprocess import Popen, PIPE, check_output
from collections import OrderedDict, namedtuple
from leappto.providers.libvirt_provider import LibvirtMachineProvider
from leappto.version import __version__
import sys
import nmap
import time


DatabaseInfo = namedtuple('DatabaseInfo', ['name', 'username', 'password'])




# def find_unit_by(units, key, value, selector=None, comparator=None, lowercase=False):

'''
{
  'service_matchers':
    [{
      'key': 'unit_name',
      'value': 'postgresql',
      'lowercase': true,
      'match': 'leapp.models.svc.PostgreSQL'
    },
    {
      'key': 'unit_name',
      'value': 'memcached',
      'lowercase': true,
      'match': 'leapp.models.svc.Memcached'
    },
    {
      'key': 'exec_start',
      'value': 'manage.py',
      'comparator': 'any_contains',
      'match': 'leapp.models.svc.Django'
    }]
}
'''


class ServiceMatcher(object):
    #@schema(jdo='svc/matcher-1.0.0')
    def __init__(self, jdo=None):
        """ jdo -> json data object """
        






class Actor(object):
    def after(self):
        return type(None)


class DatabaseActor(Actor):
    def __init__(self, conn):
        self._db_conn = conn

    @property
    def db_conn(self):
        return self._db_conn


class FrameworkActor(Actor): pass

class PosgreSQLActor(DatabaseActor):
    @property
    def data_export_cmd(self):
        cmd = 'sudo -u {s_user} PGPASSWORD={d_password} pg_dump -F t -U {d_user} {d_name}'
        fmt = {
            's_user': 'postgres',
            'd_user': self.db_conn.username,
            'd_name': self.db_conn.name,
            'd_password': self.db_conn.password
        }
        return cmd.format(**fmt)

    @property
    def data_import_cmd(self):
        cmd = 'pg_restore -C -d postgres -F t && psql -c "ALTER USER {} PASSWORD \'{}\';"'
        return cmd.format(self.db_conn.username, self.db_conn.password)


class DjangoActor(FrameworkActor): pass


class osv3(object):
    """ OpenShift V3 API """
    class StreamCommand(Popen):
        """ Thin wrapper around subprocess.Popen """
        def __init__(self, *args, **kwargs):
            kwargs['stdout'] = PIPE
            super(osv3.StreamCommand, self).__init__(*args, **kwargs)

        def stream_command(self):
            while True:
                if self.poll() is not None:
                    break
                line = self.stdout.readline()
                if line:
                    yield line[:-1] # strip new line at the end and yield

    @staticmethod
    def oc_stream(command, streaming_printer):
        cmd = osv3.StreamCommand(['oc'] + command)
        for line in cmd.stream_command():
            streaming_printer(line)
        return cmd.wait()

    @staticmethod
    def oc_exec(name, command, **kwargs):
        return Popen(['oc', 'exec', '-i', name, '--'] + command, **kwargs).wait()

    @staticmethod
    def oc(command):
        return check_output(['oc'] + command)

    class BuildDefinition(object):
        def __init__(self, strategy=None, docker_image=None, to=None, args=None, from_dir=None, follow=False):
            # OpenShift variables
            self._strategy = strategy
            self._docker_image = docker_image
            self._to = to
            self._args = args or []
            self._from_dir = from_dir
            self._follow = follow

        def args_append(self, args, attr):
            try:
                attribute = getattr(self, '_' + attr)
                args += ['--{}={}'.format(attr.replace('_', '-'), attribute)]
            except AttributeError:
                pass

        def create_build(self):
            args = ['new-build']
            self.args_append(args, 'strategy')
            self.args_append(args, 'to')
            self.args_append(args, 'docker_image')
            args += ['--name', self._to]
            args += [self._args]
            return args

        def create_build_and_start(self):
            build = self.create_build()

            args = ['start-build']
            self.args_append(args, 'from_dir')
            self.args_append(args, 'follow')
            args += [self._to]

            return {'build': build, 'start': args}

    class BuildError(Exception): pass

    class sync(object):
        class Periodic(object):
            def __init__(self, callback, frequency):
                assert callback and frequency > 0, 'Invalid periodic object'

                self._callback = callback
                self._frequency = frequency

            @property
            def callback(self):
                return self._callback

            @property
            def frequency(self):
                return self._frequency

        class TimeoutExceededError(Exception): pass

        @staticmethod
        def NewSourceBuild(definition=None):

            assert isinstance(definition, osv3.BuildDefinition), 'definition must be osv3.BuildDefinition'

            build_def = definition.create_build_and_start()
            printer = None

            osv3.oc(build_def['build'])

            if definition._follow:
                def p(x):
                    print(x)
                if osv3.oc_stream(build_def['start'], p) != 0:
                    raise osv3.BuildError
                return

            osv3.oc(build_def['start'])


        """ Synchronization helpers """
        @staticmethod
        def Pod(name=None, timeout=None, readiness=True, periodic=None):

            assert isinstance(name, str) and name, 'Name is mandatory not empty string'
            assert timeout > 0, 'Timeout must be greater than zero'
            assert isinstance(readiness, bool), 'Readiness must be bool value'
            assert isinstance(periodic, osv3.sync.Periodic), 'periodic must be of type osv3.sync.Periodic'

            delta = 0 if not periodic else periodic.frequency

            pod = None
            deadline = time.time() + timeout
            next_message = time.time() + delta

            while True:
                if time.time() >= deadline:
                    raise osv3.sync.TimeoutExceededError
                if periodic.callback and time.time() >= next_message:
                    periodic.callback()
                    next_message = time.time() + delta
                if not pod:
                    cmd = ["get", "-o", "jsonpath", "pod",
                           "--selector=name={}".format(name),
                           "--template={.items[*].metadata.name}"]
                    pod = str(osv3.oc(cmd))
                time.sleep(delta)
                if pod:
                    if readiness:
                        cmd = ['get', 'po', pod, '--output', 'jsonpath', '--template', '{.status.containerStatuses.*.ready}']
                        if 'true' in str(osv3.oc(cmd)):
                            return pod
                    else:
                        return pod

        @staticmethod
        def ProcessApply(file, variables=None):
            """ Execute process -> apply template expansion  """

            assert isinstance(file, str) and len(file) > 0, 'File must be non empty string'

            variables = variables or []
            proc = ['oc', 'process', '-f', file]
            for var in variables:
                proc += ['-v', var]
            p = Popen(proc, stdout=PIPE)
            apply = ['oc', 'apply', '-f', '-']
            a = Popen(apply, stdin=p.stdout).wait()
            return p.wait() == 0


def _ssh_config(username, identity):
    assert username is not None and isinstance(username, str), "username should be str or None"
    assert isinstance(identity, str), "identity should be str"

    settings = {
        'StrictHostKeyChecking': 'no',
        'PasswordAuthentication': 'no',
        'IdentityFile': identity,
    }
    if username is not None:
        settings['User'] = username

    return ['-o {}={}'.format(k, v) for k, v in settings.items()]


def _ssh_base(cfg, tgt):
    return ['ssh'] + cfg + ['-4', tgt]


def _ssh(cfg, tgt, cmd, **kwargs):
    arg = _ssh_base(cfg, tgt) + cmd
    print(" ".join(arg))
    return Popen(arg, **kwargs).wait()

def _ssh_output(cfg, tgt, cmd):
    arg = _ssh_base(cfg, tgt) + cmd
    return check_output(arg)


def get_value(obj, pathspec, default=None, strict=False):
    if '.' not in pathspec and pathspec not in obj:
        if strict:
            raise ValueError('pathspec: "{}" is invalid'.format(pathspec))
        return default
    bound = obj
    for item in pathspec.split('.'):
        if item in bound:
            bound = bound[item]
        else:
            if strict:
                raise ValueError('pathspec: "{}" is invalid'.format(pathspec))
            return default
    return bound


def get_items(obj, *items):
    i = []
    for item in items:
        i.append(obj[item])
    return i


def get_db_connection(db_info):
    return DatabaseInfo(*get_items(db_info, 'NAME', 'USER', 'PASSWORD'))


def get_data_from_metadata(metadata):
    # handle only the first django element
    db_dict = get_value(metadata['django'][0], 'data.db.default')
    return get_db_connection(db_dict)


def migrate_microservices_v2(source_ip, target_ip, openshift, identity, user):
    ANALYZER_PATH = '/opt/leapp-to/analyzers/django'

    os_user, os_pw = openshift.split(':')
    ssh_config = _ssh_config(user, identity)

    def scp(src, dst):
        """ Copy files from src to dst using `scp -r` and local ssh config """
        import os
        return Popen(['scp', '-r'] + ssh_config + [src, dst], stdout=open(os.devnull, 'w')).wait()

    def ssh(cmd, **kwargs):
        """ Execute SSH command using local ssh config  """
        return _ssh(ssh_config, source_ip, cmd, **kwargs)

    def ssh_output(cmd):
        """ Wrap our kludge _ssh_output funtion with local ssh config """
        return _ssh_output(ssh_config, source_ip, cmd)


    print('! Creating remote tmp dir')
    ## = COPY IN THE DATA ====================================================
    tmp_dir = ssh_output(['mktemp', '-d']).strip()
    print('! Copying analyzer into remote tmp dir: {}'.format(tmp_dir))
    scp(ANALYZER_PATH, source_ip+':'+tmp_dir)

    ## = EXECUTE ANALYZER ====================================================
    print('! Executing analyzer remotely')
    metadata = loads(ssh_output(['python ' + path.join(tmp_dir, 'django/django_analyzer_impl.py')]))
    import pprint
    print('! Analyzer data:')
    pprint.pprint(metadata)

    print('! Connecting to OpenShift: {}@{}'.format(os_user, target_ip))
    osv3.oc(['login', '-u', os_user, '-p', os_pw, 'https://{}:8443/'.format(target_ip)])

    ## = USE DATA ============================================================
    db_conn = get_data_from_metadata(metadata)

    print('! Starting PostgreSQL Pod & Services')

    # Refactor into actors.matchers.Memcached[KVSImage] and actors.matchers.PostgreSQL[DatabaseImage]
    # ------
    #
    # Matchers are responsible for detecting the given service represented by the actor in
    # the service metadata files.
    # Basically, service data are processed by actors.matchers.Registry[Actor] which is a registry
    # of actor matchers with `match_actors` method returning a list of all matched actors.
    #
    # Each actor receives a reference to the original service data and custom state/tag?.


    osv3.sync.ProcessApply('/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-memcached.yaml', [])
    osv3.oc(['apply', '-f', '/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-memcached-svc.yaml'])
    osv3.sync.ProcessApply('/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-postgresql.yaml', ['POSTGRESQL_VERSION=9.2'])
    pod_name = None

    def pp():
        print(' > waiting for pod to become ready')
    periodic = osv3.sync.Periodic(pp, 5)

    try:
        pod_name = osv3.sync.Pod('postgresql', periodic=periodic, timeout=180)
    except osv3.sync.TimeoutExceededError:
        print('Unable to get the pod withing specified timeout')
        exit(-1)

    #print('! Waiting for the pod to become ready ...')
    #time.sleep(30)
    print('! Running PostgreSQL pod: ' + pod_name)
    create_user = 'PGPASSWORD={pw} createuser {un}'.format(pw=db_conn.password, un=db_conn.username)
    # race here
    osv3.oc_exec(pod_name, ['bash', '-c', create_user])

    with NamedTemporaryFile() as tmp:
        cmd = 'sudo -u {s_user} PGPASSWORD={d_password} pg_dump -F t -U {d_user} {d_name}'
        fmt = {
            's_user': 'postgres',
            'd_user': db_conn.username,
            'd_name': db_conn.name,
            'd_password': db_conn.password
        }
        ssh([cmd.format(**fmt)], stdout=tmp)
        print('! Database backup snapshotted in: {} ({} bytes) '.format(tmp.name, path.getsize(tmp.name)))

        tmp.seek(0)
        # need to know name of pg_restore
        # PostgreSQLImage[DatabaseImage] -> { data_restore_cmd: command:str, <file> }
        osv3.oc_exec(pod_name, ['bash', '-c', "pg_restore -C -d postgres -F t"], stdin=tmp)
        print('! Setting password for user: {}'.format(db_conn.username))
        # need to know name of psql
        # PostgreSQLImage[DatabaseImage] -> { data_set_user_password: command:str, <fn(username:str, password:str)> }
        osv3.oc_exec(pod_name, ['bash', '-c', 'psql -c "ALTER USER {} PASSWORD \'{}\';"'.format(db_conn.username, db_conn.password)])

    ## =======================================================================
    print('! Copying application source to artifacts')
    src_path = metadata['django'][0]['path']
    app_source_dir = mkdtemp()
    scp(source_ip+':'+src_path, app_source_dir)

    print('! Updating configuration before deployment')
    mocked_settings_py = path.relpath(metadata['django'][0]['settings'][0], src_path)
    with open(path.join(app_source_dir, 'blog', mocked_settings_py), 'w+') as spy:
        print('! Updated file: \n' + pprint.pformat(metadata['django'][0]['deploy_settings']))
        spy.write(metadata['django'][0]['deploy_settings'][0]['detail'])
    ## =======================================================================

    print('! Compressing sources')
    check_output(['tar', '--format=gnu', '-cvf', '/tmp/deploy.tar', '-C', app_source_dir+'/'+'blog/', '.'])


    bd = osv3.BuildDefinition(strategy='source', docker_image='centos/python-27-centos7',
                              to='django-mezza', args=app_source_dir+'/'+'blog/',
                              from_dir='/tmp/deploy.tar', follow=True)

    osv3.sync.NewSourceBuild(bd)


    #print('! Creating S2I Build config')
    #oc(['new-build', '--strategy=source', '--docker-image=centos/python-27-centos7', '--to=django-mezza', app_source_dir+'/'+'blog/'])
    # racing here
    #time.sleep(2)
    #print('! Running S2I Build')
    #oc(['start-build', '--from-dir=/tmp/deploy.tar', 'django-mezza'])
    #print('! Listening to build events ...')
    #oc(['logs', '-f', 'django-mezza-1-build'])

    osv3.oc(['new-app', 'django-mezza'])
    osv3.oc(['expose', 'service', '--port', '8080', 'django-mezza'])
    osv3.oc(['get', 'route'])
    osv3.oc(['get', 'svc'])
    ## =======================================================================


def migrate_microservices(source_ip, target_ip, openshift, identity, user):
    ANALYZER_PATH = '/opt/leapp-to/analyzers/django'

    os_user, os_pw = openshift.split(':')
    ssh_config = _ssh_config(user, identity)

    def scp(src, dst):
        """ Copy files from src to dst using `scp -r` and local ssh config """
        import os
        return Popen(['scp', '-r'] + ssh_config + [src, dst], stdout=open(os.devnull, 'w')).wait()

    def ssh(cmd, **kwargs):
        """ Execute SSH command using local ssh config  """
        return _ssh(ssh_config, source_ip, cmd, **kwargs)

    def ssh_output(cmd):
        """ Wrap our kludge _ssh_output funtion with local ssh config """
        return _ssh_output(ssh_config, source_ip, cmd)

    def oc(cmd, **kwargs):
        """ Execute and echo openshift command  """
        print('oc ' + ' '.join(cmd))
        return Popen(['oc'] + cmd, **kwargs).wait()

    def oc_process_apply(variables, file):
        """ Execute process -> apply template expansion  """
        proc = ['oc', 'process', '-f', file]
        for var in variables:
            proc += ['-v', var]
        p = Popen(proc, stdout=PIPE)
        apply = ['oc', 'apply', '-f', '-']
        a = Popen(apply, stdin=p.stdout).wait()
        p.wait()

    def oc_get_pod_name(selector):
        """ Get runtime pod name using a configuratin time name """
        sel = ["oc", "get", "-o", "jsonpath", "pod",
               "--selector=name={}".format(selector),
               "--template={.items[*].metadata.name}"]
        return check_output(sel)

    def oc_get_pod_readiness(name):
        cmd = ['oc', 'get', 'po', name, '--output', 'jsonpath', '--template', '{.status.containerStatuses.*.ready}']
        return 'true' in str(check_output(cmd))

    print('! Creating remote tmp dir')
    ## = COPY IN THE DATA ====================================================
    tmp_dir = ssh_output(['mktemp', '-d']).strip()
    print('! Copying analyzer into remote tmp dir: {}'.format(tmp_dir))
    scp(ANALYZER_PATH, source_ip+':'+tmp_dir)

    ## = EXECUTE ANALYZER ====================================================
    print('! Executing analyzer remotely')
    metadata = loads(ssh_output(['python ' + path.join(tmp_dir, 'django/django_analyzer_impl.py')]))
    import pprint
    print('! Analyzer data:')
    pprint.pprint(metadata)

    print('! Connecting to OpenShift: {}@{}'.format(os_user, target_ip))
    oc(['login', '-u', os_user, '-p', os_pw, 'https://{}:8443/'.format(target_ip)])

    ## = USE DATA ============================================================
    db_conn = get_data_from_metadata(metadata)

    print('! Starting PostgreSQL Pod & Services')

    # Refactor into actors.matchers.Memcached[KVSImage] and actors.matchers.PostgreSQL[DatabaseImage]
    # ------
    #
    # Matchers are responsible for detecting the given service represented by the actor in
    # the service metadata files.
    # Basically, service data are processed by actors.matchers.Registry[Actor] which is a registry
    # of actor matchers with `match_actors` method returning a list of all matched actors.
    #
    # Each actor receives a reference to the original service data and custom state/tag?.
    oc_process_apply([], '/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-memcached.yaml')
    time.sleep(1)
    oc(['apply', '-f', '/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-memcached-svc.yaml'])
    time.sleep(1)
    oc_process_apply(['POSTGRESQL_VERSION=9.2'], '/home/podvody/Repos/leapp-proto/src/leappto/playground/artifacts/openshift-postgresql.yaml')
    # verify the above operations succeeded

    pgsql_pod = None
    deadline = time.time() + 120
    next_message = time.time() + 2
    print('! Waiting for PostgreSQL pod to become active and ready ...')
    while True:
        if time.time() >= deadline:
            print(' > deadline passed, exiting')
            exit(-1)
        if time.time() >= next_message:
            print(' > still waiting')
            next_message = time.time() + 2
        if not pgsql_pod:
            pgsql_pod = oc_get_pod_name('postgresql')
        time.sleep(1)
        if pgsql_pod:
            if oc_get_pod_readiness(pgsql_pod):
                break

    #print('! Waiting for the pod to become ready ...')
    #time.sleep(30)
    print('! Running PostgreSQL pod: ' + pgsql_pod)
    create_user = 'PGPASSWORD={pw} createuser {un}'.format(pw=db_conn.password, un=db_conn.username)
    # race here
    oc(['exec', pgsql_pod, '--', 'bash', '-c', create_user])

    with NamedTemporaryFile() as tmp:
        cmd = 'sudo -u {s_user} PGPASSWORD={d_password} pg_dump -F t -U {d_user} {d_name}'
        fmt = {
            's_user': 'postgres',
            'd_user': db_conn.username,
            'd_name': db_conn.name,
            'd_password': db_conn.password
        }
        ssh([cmd.format(**fmt)], stdout=tmp)
        print('! Database backup snapshotted in: {} ({} bytes) '.format(tmp.name, path.getsize(tmp.name)))

        tmp.seek(0)
        # need to know name of pg_restore
        # PostgreSQLImage[DatabaseImage] -> { data_restore_cmd: command:str, <file> }
        oc(['exec', '-i', pgsql_pod, '--', 'bash', '-c', "pg_restore -C -d postgres -F t"], stdin=tmp)
        print('! Setting password for user: {}'.format(db_conn.username))
        # need to know name of psql
        # PostgreSQLImage[DatabaseImage] -> { data_set_user_password: command:str, <fn(username:str, password:str)> }
        oc(['exec', '-i', pgsql_pod, '--', 'bash', '-c', 'psql -c "ALTER USER {} PASSWORD \'{}\';"'.format(db_conn.username, db_conn.password)], stdin=tmp)

    ## =======================================================================
    print('! Copying application source to artifacts')
    src_path = metadata['django'][0]['path']
    app_source_dir = mkdtemp()
    scp(source_ip+':'+src_path, app_source_dir)

    print('! Updating configuration before deployment')
    mocked_settings_py = path.relpath(metadata['django'][0]['settings'][0], src_path)
    with open(path.join(app_source_dir, 'blog', mocked_settings_py), 'w+') as spy:
        print('! Updated file: \n' + pprint.pformat(metadata['django'][0]['deploy_settings']))
        spy.write(metadata['django'][0]['deploy_settings'][0]['detail'])
    ## =======================================================================

    print('! Compressing sources')
    check_output(['tar', '--format=gnu', '-cvf', '/tmp/deploy.tar', '-C', app_source_dir+'/'+'blog/', '.'])

    print('! Creating S2I Build config')
    oc(['new-build', '--strategy=source', '--docker-image=centos/python-27-centos7', '--to=django-mezza', app_source_dir+'/'+'blog/'])

    # racing here
    time.sleep(2)
    print('! Running S2I Build')
    oc(['start-build', '--from-dir=/tmp/deploy.tar', 'django-mezza'])

    print('! Listening to build events ...')
    oc(['logs', '-f', 'django-mezza-1-build'])
    oc(['new-app', 'django-mezza'])
    oc(['expose', 'service', '--port', '8080', 'django-mezza'])
    oc(['get', 'route'])
    oc(['get', 'svc'])
    ## =======================================================================


VERSION='leapp-tool {0}'.format(__version__)

# Checking for required permissions
_REQUIRED_GROUPS = ["vagrant", "libvirt"]
def _user_has_required_permissions():
    """Check user has necessary permissions to reliably run leapp-tool"""
    uid = getuid()
    if uid == 0:
        # root has the necessary access regardless of group membership
        return True
    user_info = getpwuid(uid)
    user_name = user_info.pw_name
    user_group = getgrgid(user_info.pw_gid).gr_name
    for group in _REQUIRED_GROUPS:
        if group != user_group and user_name not in getgrnam(group).gr_mem:
            return False
    return True

# Parsing CLI arguments
def _add_identity_options(cli_cmd):
    cli_cmd.add_argument('--identity', default=None, help='Path to private SSH key')
    cli_cmd.add_argument('--user', '-u', default=None, help='Connect as this user')

def _make_argument_parser():
    ap = ArgumentParser()
    ap.add_argument('-v', '--version', action='version', version=VERSION, help='display version information')
    parser = ap.add_subparsers(help='sub-command', dest='action')

    list_cmd = parser.add_parser('list-machines', help='list running virtual machines and some information')
    migrate_cmd = parser.add_parser('migrate-machine', help='migrate source VM to a target container host')
    destroy_cmd = parser.add_parser('destroy-containers', help='destroy existing containers on virtual machine')
    scan_ports_cmd = parser.add_parser('port-inspect', help='scan ports on virtual machine')
    microservices_cmd = parser.add_parser('microservices', help='migrate source VM to a target OpenShift cluster')

    list_cmd.add_argument('--shallow', action='store_true', help='Skip detailed scans of VM contents')
    list_cmd.add_argument('pattern', nargs='*', default=['*'], help='list machines matching pattern')

    def _port_spec(arg):
        """Converts a port forwarding specifier to a (host_port, container_port) tuple

        Specifiers can be either a simple integer, where the host and container port are
        the same, or else a string in the form "host_port:container_port".
        """
        host_port, sep, container_port = arg.partition(":")
        host_port = int(host_port)
        if sep is None:
            container_port = host_port
        else:
            container_port = int(container_port)
        return host_port, container_port

    migrate_cmd.add_argument('machine', help='source machine to migrate')
    migrate_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    migrate_cmd.add_argument(
        '--tcp-port',
        default=None,
        dest="forwarded_ports",
        nargs='*',
        type=_port_spec,
        help='Target ports to forward to macrocontainer (temporary!)'
    )
    _add_identity_options(migrate_cmd)

    destroy_cmd.add_argument('target', help='target VM name')
    _add_identity_options(destroy_cmd)

    scan_ports_cmd.add_argument('range', help='port range, example of proper form:"-100,200-1024,T:3000-4000,U:60000-"')
    scan_ports_cmd.add_argument('ip', help='virtual machine ip address')

    microservices_cmd.add_argument('source', help='source machine to migrate')
    microservices_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    microservices_cmd.add_argument('-o', '--openshift-credentials', default='developer:developer', help='credentials to use to access target OpenShift cluster in the username:password format')
    _add_identity_options(microservices_cmd)

    return ap

# Run the CLI
def main():
    if not _user_has_required_permissions():
        msg = "Run leapp-tool as root, or as a member of all these groups: "
        print(msg + ",".join(_REQUIRED_GROUPS))
        exit(-1)

    ap = _make_argument_parser()

    def _find_machine(ms, name):
        for machine in ms:
            if machine.hostname == name:
                return machine
        return None

    def _set_ssh_config(username, identity):
        if not isinstance(identity, str):
            raise TypeError("identity should be str")
        settings = {
            'StrictHostKeyChecking': 'no',
            'PasswordAuthentication': 'no',
            'IdentityFile': identity,
        }
        if username is not None:
            if not isinstance(username, str):
                raise TypeError("username should be str")
            settings['User'] = username

        return ['-o {}={}'.format(k, v) for k, v in settings.items()]

    class MigrationContext:
        def __init__(self, target, target_cfg, disk, forwarded_ports=None):
            self.target = target
            self.target_cfg = target_cfg
            self.disk = disk
            if forwarded_ports is None:
                forwarded_ports = [(80, 80)]  # Default to forwarding plain HTTP
            else:
                forwarded_ports = list(forwarded_ports)
            forwarded_ports.append((9022, 22))  # Always forward SSH
            self.forwarded_ports = forwarded_ports

        @property
        def _ssh_base(self):
            return ['ssh'] + self.target_cfg + ['-4', self.target]

        def _ssh(self, cmd, **kwargs):
            arg = self._ssh_base + [cmd]
            return Popen(arg, **kwargs).wait()

        def _ssh_sudo(self, cmd, **kwargs):
            return self._ssh("sudo bash -c '{}'".format(cmd), **kwargs)

        def copy(self):
            # Vagrant always uses qemu:///system, so for now, we always run
            # virt-tar-out as root, rather than as the current user
            proc = Popen(['sudo', 'virt-tar-out', '-a', self.disk, '/', '-'], stdout=PIPE)
            return self._ssh('cat > /opt/leapp-to/container.tar.gz', stdin=proc.stdout)

        def destroy_containers(self):
            command = 'docker rm -f $(docker ps -q) 2>/dev/null 1>/dev/null; rm -rf /opt/leapp-to/container'
            return self._ssh_sudo(command)

        def start_container(self, img, init):
            command = 'docker rm -f container 2>/dev/null 1>/dev/null ; rm -rf /opt/leapp-to/container ;' + \
                    'mkdir -p /opt/leapp-to/container && ' + \
                    'tar xf /opt/leapp-to/container.tar.gz -C /opt/leapp-to/container && ' + \
                    'docker run -tid' + \
                    ' -v /sys/fs/cgroup:/sys/fs/cgroup:ro'
            good_mounts = ['bin', 'etc', 'home', 'lib', 'lib64', 'media', 'opt', 'root', 'sbin', 'srv', 'usr', 'var']
            for mount in good_mounts:
                command += ' -v /opt/leapp-to/container/{m}:/{m}:Z'.format(m=mount)
            for host_port, container_port in self.forwarded_ports:
                command += ' -p {:d}:{:d}'.format(host_port, container_port)
            command += ' --name container ' + img + ' ' + init
            return self._ssh_sudo(command)

        def _fix_container(self, fix_str):
            return self._ssh_sudo('docker exec -t container {}'.format(fix_str))

        def fix_upstart(self):
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/httpd && ' + \
                    '(service mysqld start && ' + \
                    'service httpd start) 2>/dev/null ;' + \
                    '(service drools stop ; service drools start) 2>/dev/null 1>&2"'
            return self._fix_container(fixer)

        def fix_systemd(self):
            # systemd cleans /var/log/ and mariadb & httpd can't handle that, might be a systemd bug
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/{httpd,mariadb} && ' + \
                    'chown mysql:mysql /var/log/mariadb && ' + \
                    'systemctl enable httpd mariadb ; ' + \
                    'systemctl start httpd mariadb"'
            return self._fix_container(fixer)


    parsed = ap.parse_args()
    if parsed.action == 'list-machines':
        lmp = LibvirtMachineProvider(parsed.shallow)
        print(dumps({'machines': [m._to_dict() for m in lmp.get_machines()]}, indent=3))

    elif parsed.action == 'migrate-machine':
        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")

        if not parsed.target:
            print('! no target specified, creating leappto container package in current directory')
            # TODO: not really for now
            raise NotImplementedError
        else:
            source = parsed.machine
            target = parsed.target
            forwarded_ports = parsed.forwarded_ports

            print('! looking up "{}" as source and "{}" as target'.format(source, target))

            lmp = LibvirtMachineProvider()
            machines = lmp.get_machines()

            machine_src = _find_machine(machines, source)
            machine_dst = _find_machine(machines, target)

            if not machine_dst or not machine_src:
                print("Machines are not ready:")
                print("Source: " + repr(machine_src))
                print("Target: " + repr(machine_dst))
                exit(-1)

            print('! configuring SSH keys')
            ip = machine_dst.ip[0]

            mc = MigrationContext(
                ip,
                _set_ssh_config(parsed.user, parsed.identity),
                machine_src.disks[0].host_path,
                forwarded_ports
            )
            print('! copying over')
            print('! ' + machine_src.suspend())
            mc.copy()
            print('! ' + machine_src.resume())
            print('! provisioning ...')
            # if el7 then use systemd
            if machine_src.installation.os.version.startswith('7'):
                result = mc.start_container('centos:7', '/usr/lib/systemd/systemd --system')
                print('! starting services')
                mc.fix_systemd()
            else:
                result = mc.start_container('centos:6', '/sbin/init')
                print('! starting services')
                mc.fix_upstart()
            print('! done')
            sys.exit(result)

    elif parsed.action == 'destroy-containers':
        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")
        target = parsed.target

        lmp = LibvirtMachineProvider()
        machines = lmp.get_machines()
        machine_dst = _find_machine(machines, target)

        print('! looking up "{}" as target'.format(target))
        if not machine_dst:
            print("Machine is not ready:")
            print("Target: " + repr(machine_dst))
            exit(-1)

        print('! configuring SSH keys')
        ip = machine_dst.ip[0]

        mc = MigrationContext(
            ip,
            _set_ssh_config(parsed.user, parsed.identity),
            machine_dst.disks[0].host_path
        )

        print('! destroying containers on "{}" VM'.format(target))
        mc.destroy_containers()
        print('! done')

    elif parsed.action == 'port-inspect':
        _ERR_STATE = "error"
        _SUCCESS_STATE = "success"

        port_range = parsed.range
        ip = parsed.ip
        port_scanner = nmap.PortScanner()
        port_scanner.scan(ip, port_range)

        result = {
            "status": _SUCCESS_STATE,
            "err_msg": "",
            "ports": OrderedDict()
        }

        scan_info = port_scanner.scaninfo()
        if scan_info.get('error', False):
            result["status"] = _ERR_STATE
            result["err_msg"] = scan_info['error'][0] if isinstance(scan_info['error'], list) else scan_info['error']
            print(dumps(result, indent=3))
            exit(-1)

        if ip not in port_scanner.all_hosts():
            result["status"] = _ERR_STATE
            result["err_msg"] = "Machine {} not found".format(ip)
            print(dumps(result, indent=3))
            exit(-1)

        for proto in port_scanner[ip].all_protocols():
            result['ports'][proto] = OrderedDict()
            for port in sorted(port_scanner[ip][proto]):
                if port_scanner[ip][proto][port]['state'] != 'open':
                    continue
                result['ports'][proto][port] = port_scanner[ip][proto][port]

        print(dumps(result, indent=3))

    elif parsed.action == 'microservices':
        source = parsed.source
        target = parsed.target
        openshift = parsed.openshift_credentials

        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")

        print('! looking up "{}" as source and "{}" as target'.format(source, target))

        lmp = LibvirtMachineProvider()
        machines = lmp.get_machines()

        machine_dst = _find_machine(machines, target)
        machine_src = _find_machine(machines, source)

        src_ip, dst_ip = machine_src.ip[0], machine_dst.ip[0]

        print(' > breaking up monolith at {} into microservices in {}'.format(src_ip, dst_ip))

        migrate_microservices_v2(src_ip, dst_ip, openshift, parsed.identity, parsed.user)
