import logging
import os
import sys
import uuid

from leapp.utils.meta import with_metaclass, get_flattened_subclasses
from leapp.workflows.phases import Phase
from leapp.workflows.phaseactors import PhaseActors
from leapp.messaging.inprocess import InProcessMessaging


def _phase_sorter_key(a):
    return a.get_index()


def _is_phase(attr):
    return isinstance(attr, type) and issubclass(attr, Phase)


def _get_phases_sorted(attrs):
    return tuple(sorted([attr for attr in attrs.values() if _is_phase(attr)], key=_phase_sorter_key))


class WorkflowMeta(type):
    def __new__(mcs, name, bases, attrs):
        klass = super(WorkflowMeta, mcs).__new__(mcs, name, bases, attrs)
        if not getattr(sys.modules[mcs.__module__], name, None):
            setattr(sys.modules[mcs.__module__], name, klass)
        klass.phases = _get_phases_sorted(attrs)
        return klass


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

    def __init__(self, logger=None):
        """
        :param logger: Optional logger to be used instead of leapp.workflow
        :type logger: Instance of :py:class:`logging.Logger`
        """
        self.log = (logger or logging.getLogger('leapp')).getChild('workflow')
        self._all_consumed = set()
        self._all_produced = set()
        self._initial = set()
        self._phase_actors = []

        for phase in self.phases:
            phase.filter.tags += (self.tag,)
            self._phase_actors.append((
                phase,
                self._apply_phase(phase.filter.get_before(), 'Before'),
                self._apply_phase(phase.filter.get(), 'Main'),
                self._apply_phase(phase.filter.get_after(), 'After')))

    def _apply_phase(self, actors, stage):
        phase_actors = PhaseActors(actors, stage)
        self._initial.update(set(phase_actors.initial) - self._all_produced)
        self._all_consumed.update(phase_actors.consumes)
        self._all_produced.update(phase_actors.produces)
        return phase_actors

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
        """ All consumed messaged """
        return self._all_consumed

    @property
    def produces(self):
        """ All produced messaged """
        return self._all_produced

    def run(self, execution_id=None, until_phase=None, until_actor=None):
        """
        Executes the workflow

        :param execution_id: Custom execution id to use instead of a randomly generated UUIDv4
        :type execution_id: str
        :param until_phase:
        :type until_phase:
        :param until_actor:
        :type until_actor:

        """
        os.environ['LEAPP_EXECUTION_ID'] = execution_id or str(uuid.uuid4())

        self.log.info('Starting workflow execution: {name} - ID: {id}'.format(
            name=self.name, id=os.environ['LEAPP_EXECUTION_ID']))

        needle_phase = until_phase or ''
        needle_stage = None
        if '.' in needle_phase:
            needle_phase, needle_stage = needle_phase.split('.', 1)
        needle_phase = needle_phase.lower()
        needle_stage = (needle_stage or '').lower()
        needle_actor = (until_actor or '').lower()

        for phase in self._phase_actors:
            os.environ['LEAPP_CURRENT_PHASE'] = phase[0].name

            self.log.info('Starting phase {name}'.format(name=phase[0].name))
            current_logger = self.log.getChild(phase[0].name)
            for stage in phase[1:]:
                current_logger.info("Starting stage {stage} of phase {phase}".format(
                    phase=phase[0].name, stage=stage.stage))
                for actor in stage.actors:
                    current_logger.info("Executing actor {actor}".format(actor=actor.name))
                    messaging = InProcessMessaging()
                    messaging.load(actor.consumes)
                    actor(logger=current_logger, messaging=messaging).run()

                    if needle_actor in (actor.name.lower(), actor.class_name.lower()):
                        self.log.info('Workflow finished due to until-actor flag')
                        return

                if phase[0].name.lower() == needle_phase and needle_stage == stage.stage.lower():
                    self.log.info('Workflow finished due to until-phase flag')
                    return

            if phase[0].name == needle_phase:
                self.log.info('Workflow finished due to until-phase flag')
                return


def get_workflows():
    return get_flattened_subclasses(Workflow)
