import datetime
import hashlib
import json
import multiprocessing
import os
import socket

from six.moves import configparser

from leapp.dialogs import RawMessageDialog
from leapp.dialogs.renderer import CommandlineRenderer
from leapp.messaging.answerstore import AnswerStore
from leapp.exceptions import CannotConsumeErrorMessages
from leapp.models import ErrorModel


class BaseMessaging(object):
    """
    BaseMessaging is the Base class for all messaging implementations. It provides the basic interface that is
    supported within the framework. These are called the `produce` and `consume` methods.
    """
    def __init__(self, stored=True):
        self._manager = multiprocessing.Manager()
        self._dialog_renderer = CommandlineRenderer()
        self._data = self._manager.list()
        self._answers = AnswerStore(manager=self._manager)
        self._new_data = self._manager.list()
        self._errors = self._manager.list()
        self._stored = stored

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
    def stored(self):
        """
        :return: If the messages are stored immediately, this function returns True, otherwise False.
        """
        return self._stored

    def errors(self):
        """
        Gets all produced errors.
        :return: List of newly produced errors
        """
        return list(self._errors)

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
        self._perform_load(consumes)

    def report_error(self, message, severity, actor, details):
        """
        Reports an execution error

        :param message: Message to print the error
        :type message: str
        :param severity: Severity of the error
        :type severity: ErrorSeverity
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

    def request_answers(self, dialog):
        return dialog.request_answers(self._answers, self._dialog_renderer)

    def show_message(self, message):
        """
        Used to display messages to the user

        :param message: Dialog instance to show
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
        lookup = dict([(model.__name__, model) for model in type(actor).consumes])
        if types:
            filtered = set(requested.__name__ for requested in types)
            messages = [message for message in messages if message['type'] in filtered]
        return (lookup[msg['type']].create(msg, json.loads(msg['message']['data'])) for msg in messages)
