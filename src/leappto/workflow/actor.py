""" Actors able to execute checks on our workflow """

from __future__ import print_function

from subprocess import Popen, PIPE
from wowp.actors import FuncActor


class CheckActor(FuncActor):
    """ A check actor that can be part of our workflow """
    DEFAULT_IN = 'default_in'

    def __init__(self, check_name, check_script, requires=None):
        self._check_name = check_name
        self._check_script = check_script
        self._requires = requires

        self._target_cmd = None

        if self.requires:
            super(CheckActor, self).__init__(self.__func_with_requirement,
                                             inports=[CheckActor.DEFAULT_IN,
                                                      self.requires],
                                             outports=[self.check_name+'_out'])
        else:
            super(CheckActor, self).__init__(self.__func,
                                             inports=[CheckActor.DEFAULT_IN],
                                             outports=[self.check_name+'_out'])

    @property
    def check_name(self):
        """ Return actors name """
        return self._check_name

    @property
    def check_script(self):
        """ Return script that should be executed """
        return self._check_script

    @property
    def requires(self):
        """ Return list of requires for this actor """
        return self._requires

    def __func(self, _):
        """ Method that should be executed by actor without requires"""
        script_input = open(self.check_script)
        child = Popen(self._target_cmd, stdin=script_input, stdout=PIPE, stderr=PIPE)
        out, err = child.communicate()
        return (child.returncode, out, err)

    def __func_with_requirement(self, _, require):
        """ Method that should be executed by actor with requires"""
        req_rc, req_out, req_err = require
        if req_rc:
            return(1, "", "REQUIREMENT ERROR: " + req_err)

        script_input = open(self.check_script)
        child = Popen(self._target_cmd, stdin=script_input, stdout=PIPE, stderr=PIPE)
        out, err = child.communicate()
        return (child.returncode, out, err)

    def set_target_cmd(self, target_cmd):
        """ Build command that will be executed on target machine """
        self._target_cmd = target_cmd
