import shlex
import subprocess

class Driver(object):
    def __init__(self):
        pass

    def exec_command(self, cmd):
        raise NotImplementedError()


class LocalDriver(Driver):
    def __init__(self):
        super(LocalDriver, self).__init__()

    def exec_command(self, cmd):
        args = shlex.split(cmd)
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.stdin, p.stdout, p.stderr
