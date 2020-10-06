import datetime
import hashlib
import json
import multiprocessing
import os
import socket

from six.moves import configparser

from leapp.dialogs import RawMessageDialog
from leapp.dialogs.renderer import CommandlineRenderer
from leapp.exceptions import CannotConsumeErrorMessages
from leapp.messaging.answerstore import AnswerStore
from leapp.messaging.commands import WorkflowCommand
from leapp.models import DialogModel, ErrorModel
from leapp.utils import get_api_models


class BaseMessaging(object):
    """
    BaseMessaging is the Base class for all messaging implementations. It provides the basic interface that is
    supported within the framework. These are called the `produce` and `consume` methods.
    """

    def __init__(self, stored=True, config_model=None, answer_store=None):
        self._manager = multiprocessing.Manager()
        self._dialog_renderer = CommandlineRenderer()
        self._data = self._manager.list()
        self._answers = answer_store or AnswerStore(manager=self._manager)
        self._new_data = self._manager.list()
        self._commands = self._manager.list()
        self._errors = self._manager.list()
        self._stored = stored
        self._config_models = (config_model,) if config_model else ()
        self._dialogs = self._manager.list()
        self._stop_after_phase = self._manager.Value(bool, False)

    def load_answers(self, answer_file, workflow):
        """
        Loads answers from a given answer file

        :param answer_file: Path to file to load as answer file
        :type answer_file: str
        :param workflow: :py:class:`leapp.workflows.Workflow` instance to load the answers for.
        :type workflow: :py:class:`leapp.workflows.Workflow`
        :return: None
        """
        self._answers.load_and_translate_for_workflow(answer_file, workflow)

    @property
    def commands(self):
        """
        :return: List of commands that have been sent to the workflow execution.
        """
        return list(self._commands)

    @property
    def stored(self):
        """
        :return: If the messages are stored immediately, this function returns True, otherwise False.
        """
        return self._stored

    def dialogs(self):
        """
        Gets all dialogs actually encountered during workflow run

        :return: List of encountered dialogs
        """
        return list(self._dialogs)

    def errors(self):
        """
        Gets all produced errors.

        :return: List of newly produced errors
        """
        return list(self._errors)

    @property
    def stop_after_phase(self):
        """
        Returns True if execution stop was requested after the current

        :return: True if the executed was requested to be stopped.
        """
        return self._stop_after_phase.get()

    def messages(self):
        """
        Gets all newly produced messages.

        :return: List of newly processed messages
        """
        return list(self._new_data)

    def _perform_load(self, consumes):
        """
        Loads all messages that are requested from the `consumes` attribute of :py:class:`leapp.actors.Actor`

        :param consumes: Tuple or list of :py:class:`leapp.models.Model` types to preload
        :return: None
        """
        raise NotImplementedError()

    def _process_message(self, message):
        """
        This method performs the actual message sending, which can be sent over the network or stored
        in a database.

        :param message: The message data to process
        :type message: dict
        :return: Pass through a message that might get updated through the sending process.
        """
        raise NotImplementedError()

    def load(self, consumes):
        """
        Loads all messages that are requested from the `consumes` attribute of :py:class:`leapp.actors.Actor`

        :param consumes: Tuple or list of :py:class:`leapp.models.Model` types to preload
        :return: None
        :raises leapp.exceptions.CannotConsumeErrorMessages: When trying to consume ErrorModel
        """
        if ErrorModel in consumes:
            raise CannotConsumeErrorMessages()
        self._perform_load(consumes + self._config_models)

    def report_error(self, message, severity, actor, details):
        """
        Reports an execution error

        :param message: Message to print the error
        :type message: str
        :param severity: Severity of the error
        :type severity: leapp.models.error_severity.ErrorSeverity
        :param actor: Actor name that produced the message
        :type actor: leapp.actors.Actor
        :param details: A dictionary where additional context information can be passed along with the error
        :type details: dict
        :return: None
        """
        if details:
            details = json.dumps(details)
        model = ErrorModel(message=message, actor=actor.name, severity=severity, details=details,
                           time=datetime.datetime.now())
        self._do_produce(model, actor, self._errors)

    def request_stop_after_phase(self):
        """
        If called, it will cause the workflow to stop the execution after the current phase ends.
        """
        self._stop_after_phase.set(True)

    def register_dialog(self, dialog, actor):
        self._dialogs.append(dialog)
        userchoices = dialog.get_answers(self._answers)
        if not userchoices:
            # produce DialogModel messages for all the dialogs that don't have answers in answerfile
            stable_key = dialog.key if dialog.key else hashlib.sha1(
                ','.join(sorted(dialog.answerfile_sections.keys())).encode('utf-8')).hexdigest()
            self.produce(DialogModel(actor=actor.name,
                                     answerfile_sections=dialog.answerfile_sections,
                                     key=stable_key), actor)
        else:
            # update dialogs with answers from answerfile. That is necessary for proper answerfile generation
            for component, value in userchoices.items():
                dialog_component = dialog.component_by_key(component)
                if dialog_component:
                    dialog_component.value = value

    def command(self, command):
        """
        Called to send a command to the workflow execution

        :param command: A command to send to the workflow execution.
        :type command: Instance of :py:class:`leapp.messaging.commands.WorkflowCommand`
        :return: None
        """
        if isinstance(command, WorkflowCommand):
            self._commands.append(command.encode())
        else:
            raise TypeError('Expected an instance of WorkflowCommand')

    def produce(self, model, actor):
        """
        Called to send a message available for other actors.

        :param model: Model to send as message payload
        :type model: :py:class:`leapp.models.Model`
        :param actor: Actor that sends the message
        :type actor: :py:class:`leapp.actors.Actor`
        :return: the updated message dict
        :rtype: dict
        """
        return self._do_produce(model, actor, self._new_data)

    def feed(self, model, actor):
        """
        Called to pre-fill sent messages and make them available for other actors.

        :param model: Model to send as message payload
        :type model: :py:class:`leapp.models.Model`
        :param actor: Actor that sends the message
        :type actor: :py:class:`leapp.actors.Actor`
        :return: the updated message dict
        :rtype: dict
        """
        return self._do_produce(model, actor, self._data, stored=False)

    def _do_produce(self, model, actor, target, stored=True):
        if not os.environ.get('LEAPP_HOSTNAME', None):
            os.environ['LEAPP_HOSTNAME'] = socket.getfqdn()
        data = json.dumps(model.dump(), sort_keys=True)
        message = {
            'type': type(model).__name__,
            'actor': type(actor).name,
            'topic': model.topic.name,
            'stamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'phase': os.environ.get('LEAPP_CURRENT_PHASE', 'NON-WORKFLOW-EXECUTION'),
            'context': os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'),
            'hostname': os.environ['LEAPP_HOSTNAME'],
            'message': {
                'data': data,
                'hash': hashlib.sha256(data.encode('utf-8')).hexdigest()
            }
        }

        if stored and self.stored:
            self._process_message(message.copy())

        target.append(message)
        return message

    def get_answers(self, dialog):
        # NOTE(ivasilev): Non-Interactive. Returns answer from answerfile or empty dict straightaway.
        return dialog.get_answers(self._answers)

    def request_answers(self, dialog):
        # NOTE(ivasilev): Interactive. Should not be used in actors run at preupgrade\upgrade stage.
        #                 Will render the dialog and block further execution till user makes his choice.
        return dialog.request_answers(self._answers, self._dialog_renderer)

    def show_message(self, message):
        """
        Display a message in user interterface currently in use (CLI, GUI).

        It uses one of the dialog renderers in :py:mod:`leapp.dialogs.renderer`.

        :param message: Message to show
        :type message: str
        """
        RawMessageDialog(message=message).request_answers(self._answers, self._dialog_renderer)

    def consume(self, actor, *types):
        """
        Returns all consumable messages and filters them by `types`

        :param types: Variable number of :py:class:`leapp.models.Model` derived types to filter messages to be consumed
        :param actor: Actor that consumes the data
        :return: Iterable with messages matching the criteria
        """
        types = tuple((getattr(t, '_resolved', t) for t in types))
        messages = list(self._data) + list(self._new_data)
        # Needs to use get_api_models to consider all consumes including the one specified by Workflow APIs
        lookup = {model.__name__: model for model in get_api_models(type(actor), 'consumes') + self._config_models}
        if types:
            filtered = set(requested.__name__ for requested in types)
            messages = [message for message in messages if message['type'] in filtered]
        return (lookup[message['type']].create(json.loads(message['message']['data'])) for message in messages)
