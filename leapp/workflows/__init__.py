import logging
import os
import socket
import sys
import uuid

from leapp.dialogs import RawMessageDialog
from leapp.exceptions import CommandError, MultipleConfigActorsError, WorkflowConfigNotAvailable
from leapp.messaging.answerstore import AnswerStore
from leapp.messaging.inprocess import InProcessMessaging
from leapp.messaging.commands import SkipPhasesUntilCommand
from leapp.tags import ExperimentalTag
from leapp.utils import reboot_system
from leapp.utils.audit import checkpoint, get_errors
from leapp.utils.meta import with_metaclass, get_flattened_subclasses
from leapp.workflows.phases import Phase
from leapp.workflows.policies import Policies
from leapp.workflows.phaseactors import PhaseActors


def _phase_sorter_key(a):
    return a.get_index()


def _is_phase(attr):
    return isinstance(attr, type) and issubclass(attr, Phase)


def _get_phases_sorted(attrs):
    return tuple(sorted([attr for attr in attrs.values() if _is_phase(attr)], key=_phase_sorter_key))


def actor_names(actor=None):
    return (actor.name.lower(), actor.class_name.lower()) if actor else ()


def phase_names(phase=None):
    return (phase[0].__name__.lower(), phase[0].name.lower()) if phase else ()


class WorkflowMeta(type):
    """
    Meta class for the registration of workflows
    """
    def __new__(mcs, name, bases, attrs):
        klass = super(WorkflowMeta, mcs).__new__(mcs, name, bases, attrs)
        if not getattr(sys.modules[mcs.__module__], name, None):
            setattr(sys.modules[mcs.__module__], name, klass)
        klass.phases = _get_phases_sorted(attrs)
        return klass


class _ConfigPhase(Phase):
    name = 'configuration_phase'


class Workflow(with_metaclass(WorkflowMeta)):
    """
    Workflow is the base class for all :ref:`workflow <terminology:workflow>` definitions.
    """

    name = None
    """Name of the workflow"""

    short_name = None
    """ Short name of the workflow """

    tag = None
    """ Workflow Tag """

    description = ''
    """ Documentation for the workflow """

    configuration = None
    """ Model to be used as workflow configuration """

    @property
    def errors(self):
        """
        :return: All reported errors
        """
        return self._errors

    @property
    def failure(self):
        return self._errors or self._unhandled_exception or self._stop_after_phase_requested

    @property
    def answer_store(self):
        """
        : return: AnswerStore instance used for messaging
        """
        return self._answer_store

    def save_answers(self, answerfile_path, userchoices_path):
        """
        Generates an answer file for the dialogs of the workflow and saves it to `answerfile_path`.
        Updates a .userchoices file at `userchoices_path` with new answers encountered in answerfile.

        :param answerfile_path: The path where to store the answer file.
        :param userchoices_path: The path where to store the .userchoices file.
        :return: None
        """
        # answerfile is generated only for the dialogs actually encountered in the worflow
        self._answer_store.generate(self._dialogs, answerfile_path)
        # userchoices is updated with any new data retrieved from answerfile
        self._answer_store.update(userchoices_path, allow_missing=True)

    def _load_from_file(self, filepath):
        if os.path.isfile(filepath):
            # XXX FIXME load_and_translate doesn't help here as somehow dialog.component.value
            # in Dialog.request_answers is not respectfully updated (set to None so storage
            # values are not taken into consideration).
            # Patching in 2 places - load here and direct call to translate in request_answers
            self._answer_store.load(filepath)
        else:
            self.log.warning("Previous file %s not found", filepath)

    def load_answers(self, answerfile_path, userchoices_path):
        self._load_from_file(userchoices_path)
        self._load_from_file(answerfile_path)

    def __init__(self, logger=None, auto_reboot=False):
        """
        :param logger: Optional logger to be used instead of leapp.workflow
        :type logger: Instance of :py:class:`logging.Logger`
        """
        self.log = (logger or logging.getLogger('leapp')).getChild('workflow')
        self._errors = []
        self._all_consumed = set()
        self._all_produced = set()
        self._initial = set()
        self._phase_actors = []
        self._experimental_whitelist = set()
        self._auto_reboot = auto_reboot
        self._unhandled_exception = False
        self._answer_store = AnswerStore()
        self._dialogs = []
        self._stop_after_phase_requested = False

        if self.configuration:
            config_actors = [actor for actor in self.tag.actors if self.configuration in actor.produces]
            if config_actors:
                if len(config_actors) == 1:
                    self._phase_actors.append((
                        _ConfigPhase,
                        PhaseActors((), 'Before'),
                        PhaseActors(tuple(config_actors), 'Main'),
                        PhaseActors((), 'After')))
                else:
                    config_actor_names = [a.name for a in config_actors]
                    raise MultipleConfigActorsError(config_actor_names)
        self.description = self.description or type(self).__doc__

        for phase in self.phases:
            phase.filter.tags += (self.tag,)
            self._phase_actors.append((
                phase,
                # filters all actors with the give tags
                # phasetag .Before
                self._apply_phase(phase.filter.get_before(), 'Before'),
                # phasetag
                self._apply_phase(phase.filter.get(), 'Main'),
                # phasetag .After
                self._apply_phase(phase.filter.get_after(), 'After')))

    def _apply_phase(self, actors, stage):
        phase_actors = PhaseActors(actors, stage)
        self._initial.update(set(phase_actors.initial) - self._all_produced)
        self._all_consumed.update(phase_actors.consumes)
        self._all_produced.update(phase_actors.produces)
        return phase_actors

    @property
    def experimental_whitelist(self):
        """ Whitelist of actors that may be executed even that they are marked experimental """
        return self._experimental_whitelist

    def whitelist_experimental_actor(self, actor):
        """
        Adds an actor to the experimental whitelist and allows them to be executed.

        :param actor: Actor to be whitelisted
        :type actor: class derived from py:class:`leapp.actors.Actor`
        :return: None
        """
        if actor:
            self._experimental_whitelist.add(actor)

    @property
    def phase_actors(self):
        """ Return all actors for the phase """
        return self._phase_actors

    @property
    def initial(self):
        """ Initial messages required """
        return self._initial

    @property
    def consumes(self):
        """ All consumed messages """
        return self._all_consumed

    @property
    def produces(self):
        """ All produced messages """
        return self._all_produced

    @property
    def dialogs(self):
        """ All encountered dialogs """
        return self._dialogs

    @classmethod
    def serialize(cls):
        """
        :return: Serialized form of the workflow
        """
        return {
            'name': cls.name,
            'short_name': cls.short_name,
            'tag': cls.tag.__name__,
            'description': cls.description,
            'phases': [phase.serialize() for phase in cls.phases],
        }

    def is_valid_phase(self, phase=None):
        if phase:
            return phase in [name for phs in self._phase_actors for name in phase_names(phs)]

    def run(self, context=None, until_phase=None, until_actor=None, skip_phases_until=None, skip_dialogs=False):
        """
        Executes the workflow

        :param context: Custom execution ID to be used instead of a randomly generated UUIDv4
        :type context: str
        :param until_phase: Specify until including which phase the execution should run - phase.stage can be used to
                            control it even more granularly. `phase` is any phase name where `stage` refers to `main`,
                            `before` or `after`. If no stage is defined, `after` is assumed to be the default value.
                            The execution ends when this phase (and stage, if specified) has been executed.
        :type until_phase: str
        :param until_actor: The execution finishes when this actor has been executed.
        :type until_actor: str
        :param skip_phases_until: Skips all phases until including the phase specified, and then continues the
               execution.
        :type skip_phases_until: str or None
        :param skip_dialogs: Inform actors about the mode of dialogs processing. If skip_dialogs is set to True it
                             means that dialogs can't be processed in the current workflow run interactively and
                             every attempted call of get_answers api method will be non-blocking, returning an empty
                             dict if no user choice was found in answerfile or a selected option otherwise.
                             If skip_dialogs is set to False then in case of absent recorded answer the dialog will
                             be rendered in a blocking user input requiring way.
                             The value of skip_dialogs will be passed to the actors that can theoretically use it for
                             their purposes.
        :type skip_dialogs: bool

        """
        context = context or str(uuid.uuid4())
        os.environ['LEAPP_EXECUTION_ID'] = context
        if not os.environ.get('LEAPP_HOSTNAME', None):
            os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()

        self.log.info('Starting workflow execution: {name} - ID: {id}'.format(
            name=self.name, id=os.environ['LEAPP_EXECUTION_ID']))

        skip_phases_until = (skip_phases_until or '').lower()
        needle_phase = until_phase or ''
        needle_stage = None
        if '.' in needle_phase:
            needle_phase, needle_stage = needle_phase.split('.', 1)
        needle_phase = needle_phase.lower()
        needle_stage = (needle_stage or '').lower()
        needle_actor = (until_actor or '').lower()

        self._errors = get_errors(context)
        config_model = type(self).configuration

        for phase in skip_phases_until, needle_phase:
            if phase and not self.is_valid_phase(phase):
                raise CommandError('Phase {phase} does not exist in the workflow'.format(phase=phase))

        self._stop_after_phase_requested = False
        for phase in self._phase_actors:
            os.environ['LEAPP_CURRENT_PHASE'] = phase[0].name
            if skip_phases_until:
                if skip_phases_until in phase_names(phase):
                    skip_phases_until = ''
                self.log.info('Skipping phase {name}'.format(name=phase[0].name))
                continue

            self.log.info('Starting phase {name}'.format(name=phase[0].name))
            current_logger = self.log.getChild(phase[0].name)

            early_finish = False
            for stage in phase[1:]:
                if early_finish:
                    return
                current_logger.info("Starting stage {stage} of phase {phase}".format(
                    phase=phase[0].name, stage=stage.stage))
                for actor in stage.actors:
                    if early_finish:
                        return
                    designation = ''
                    if ExperimentalTag in actor.tags:
                        designation = '[EXPERIMENTAL]'
                        if actor not in self.experimental_whitelist:
                            current_logger.info("Skipping experimental actor {actor}".format(actor=actor.name))
                            continue
                    current_logger.info("Executing actor {actor} {designation}".format(designation=designation,
                                                                                       actor=actor.name))
                    messaging = InProcessMessaging(config_model=config_model, answer_store=self._answer_store)
                    messaging.load(actor.consumes)
                    instance = actor(logger=current_logger, messaging=messaging,
                                     config_model=config_model, skip_dialogs=skip_dialogs)
                    try:
                        instance.run()
                    except BaseException:
                        self._unhandled_exception = True
                        raise

                    self._stop_after_phase_requested = messaging.stop_after_phase or self._stop_after_phase_requested

                    # Collect dialogs
                    self._dialogs.extend(messaging.dialogs())
                    # Collect errors
                    if messaging.errors():
                        self._errors.extend(messaging.errors())

                        if phase[0].policies.error is Policies.Errors.FailImmediately:
                            self.log.info('Workflow interrupted due to FailImmediately error policy')
                            early_finish = True
                            break

                    for command in messaging.commands:
                        if command['command'] == SkipPhasesUntilCommand.COMMAND:
                            skip_phases_until = command['arguments']['until_phase']
                            self.log.info('SkipPhasesUntilCommand received. Skipping phases until {}'.format(
                                skip_phases_until))

                    checkpoint(actor=actor.name, phase=phase[0].name, context=context,
                               hostname=os.environ['LEAPP_HOSTNAME'])
                    if needle_actor in actor_names(actor):
                        self.log.info('Workflow finished due to the until-actor flag')
                        early_finish = True
                        break
                if not stage.actors:
                    checkpoint(actor='', phase=phase[0].name + '.' + stage.stage, context=context,
                               hostname=os.environ['LEAPP_HOSTNAME'])

                if needle_phase in phase_names(phase) and needle_stage == stage.stage.lower():
                    self.log.info('Workflow finished due to the until-phase flag')
                    early_finish = True
                    break

            checkpoint(actor='', phase=phase[0].name, context=context, hostname=os.environ['LEAPP_HOSTNAME'])

            if self._errors and phase[0].policies.error is Policies.Errors.FailPhase:
                self.log.info('Workflow interrupted due to the FailPhase error policy')
                early_finish = True

            elif needle_phase in phase_names(phase):
                self.log.info('Workflow finished due to the until-phase flag')
                early_finish = True

            elif self._stop_after_phase_requested:
                self.log.info('Workflow received request to stop after phase.')
                early_finish = True

            elif phase[0].flags.request_restart_after_phase or phase[0].flags.restart_after_phase:
                reboot = True
                if phase[0].flags.request_restart_after_phase and not self._auto_reboot:
                    reboot = False
                    messaging.request_answers(
                        RawMessageDialog(message='A reboot is required to continue. Please reboot your system.')
                    )
                if reboot:
                    self.log.info('Initiating system reboot due to the restart_after_reboot flag')
                    reboot_system()
                early_finish = True

            elif phase[0].flags.is_checkpoint:
                self.log.info('Stopping the workflow execution due to the is_checkpoint flag')
                early_finish = True

            if early_finish:
                return


def get_workflows():
    """
    :return: all registered workflows
    """
    return get_flattened_subclasses(Workflow)
