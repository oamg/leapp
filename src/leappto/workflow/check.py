""" Check functions implemented using Workflow programming """

from __future__ import print_function

import shlex
from json import dumps
from wowp.actors import FuncActor, DictionaryMerge
from leappto.providers.libvirt import LibvirtMachineProvider
from leappto.workflow.actor import CheckActor


class CheckWorkflow(object):
    """ Manage dependencies between actors and execute workflow """
    LOCALHOST_IP = '127.0.0.1'

    def __init__(self, hostname, user=None, identity=None, shallow=True):
        self._target_hostname = hostname
        self._target_ip = self.__get_hostname_ip(shallow)
        self._user = user
        self._identity = identity
        self._actors = {}

    @property
    def target_hostname(self):
        """ Return machine hostname where workflow will be executed """
        return self._target_hostname

    @property
    def target_ip(self):
        """ Return machine IP where workflow will be executed """
        return self._target_ip

    @property
    def user(self):
        """ Return user provided to access target machine """
        return self._user

    @property
    def identity(self):
        """ Return identity provided to access target machine """
        return self._identity

    @property
    def is_local_machine(self):
        """ Return if target machine is local """
        return self.target_ip == self.LOCALHOST_IP

    def __get_hostname_ip(self, shallow):
        """ Find target IP """
        if self._target_hostname in ('localhost', self.LOCALHOST_IP):
            return self.LOCALHOST_IP
        else:
            lmp = LibvirtMachineProvider(shallow)
            machines = lmp.get_machines()
            for machine in machines:
                if machine.hostname == self.target_hostname:
                    return machine.ip[0]
        return None

    def __get_ssh_options(self):
        """ Return ssh options used to access machine via SSH """
        settings = {
            'StrictHostKeyChecking': 'no',
            'PasswordAuthentication': 'no'
        }

        if self.user is not None:
            if not isinstance(self.user, str):
                raise TypeError("Provided user should be str")
            settings['User'] = self.user

        if self.identity is not None:
            if not isinstance(self.identity, str):
                raise TypeError("Provided identity should be str")
            settings['IdentityFile'] = self.identity

        ssh_opt = ['-o {}={}'.format(k, v) for k, v in settings.items()]
        return ssh_opt

    def __get_exec_cmd(self, cmd):
        """ Return command line that should be executed on target machine """
        sudo_cmd = "sudo bash -c '{}'".format(cmd)
        if self.is_local_machine:
            return shlex.split(sudo_cmd)

        ssh_cmd = ['ssh']
        ssh_cmd += self.__get_ssh_options()
        ssh_cmd += ['-4', self.target_ip]
        ssh_cmd += [sudo_cmd]
        return ssh_cmd

    def add_actor(self, actor):
        """ Add actor to workflow """
        actor.set_target_cmd(self.__get_exec_cmd(actor.check_cmd))
        self._actors[actor.check_name] = actor

    def run(self):
        """ Execute check workflow """

        def start_workflow(hostname):
            """ Simple function to trigger all other actors """
            return hostname

        start_actor = FuncActor(start_workflow, outports=['out'])

        input_dict = {}
        output_dict = {}
        for _, actor in self._actors.iteritems():
            for inport in actor.inports:
                if inport.name == CheckActor.DEFAULT_IN:
                    inport += start_actor.outports['out']
                else:
                    input_dict[inport.name] = actor

            for outport in actor.outports:
                output_dict[outport.name] = actor

        for port, actor in input_dict.iteritems():
            if port in self._actors:
                actor.inports[port] += self._actors[port].outports[port + '_out']
            else:
                print("Missing requirement ({}) for actor ({})".format(port, actor.check_name))

        dict_actor = DictionaryMerge(inport_names=output_dict.keys(), outport_name='out')

        for port, actor in output_dict.iteritems():
            dict_actor.inports[port] += actor.outports[port]

        workflow = dict_actor.get_workflow()
        ret_workflow = workflow(hostname=self.target_hostname)
        print(dumps(ret_workflow['out'].pop(), indent=2))
