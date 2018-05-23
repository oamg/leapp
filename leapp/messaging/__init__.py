import datetime
import hashlib
import json
import multiprocessing
import os
import socket

from leapp.dialogs.renderer import CommandlineRenderer
from leapp.exceptions import CannotConsumeErrorMessages
from leapp.models import ErrorModel


class BaseMessaging(object):
    """
    BaseMessaging is the Base class for all messaging implementations - It provides the basic interface that is
    supported within the framework - That are the `produce` and `consume` methods.
    """
    def __init__(self, stored=True):
        self._manager = multiprocessing.Manager()
        self._dialog_renderer = CommandlineRenderer()
        self._data = self._manager.list()
        self._answers = self._manager.dict()
        self._new_data = self._manager.list()
        self._errors = self._manager.list()
        self._stored = stored

    @property
    def stored(self):
        """
        :return: If the messages are stored immediately this returns True otherwise False
        """
        return self._stored

    def errors(self):
        """
        Get all produced errors
        :return: List of newly produced errors
        """
        return list(self._errors)

    def messages(self):
        """
        Get all newly produced messages
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
        This method should perform the actual message sending - Which could be sending it over the network or storing
        it in a database.

        :param message: The message data to process
        :type message: dict
        :return: Pass through message which might get updated through the sending process
        """
        raise NotImplementedError()

    def load(self, consumes):
        """
        Loads all messages that are requested from the `consumes` attribute of :py:class:`leapp.actors.Actor`

        :param consumes: Tuple or list of :py:class:`leapp.models.Model` types to preload
        :return: None
        :raises leapp.exceptions.CannotConsumeErrorMessages: When an trying to consume ErrorModel
        """
        if ErrorModel in consumes:
            raise CannotConsumeErrorMessages()
        self._perform_load(consumes)

    def report_error(self, message, severity, actor, details):
        """
        Reports an execution error

        :param message: Message to print for the error
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
                           time=datetime.datetime.utcnow())
        self._do_produce(model, actor, self._errors)

    def produce(self, model, actor):
        """
        Called to send a message to be available for other actors.

        :param model: Model to send as message payload
        :type model: :py:class:`leapp.models.Model`
        :param actor: Actor that sends the message
        :type actor: :py:class:`leapp.actors.Actor`
        :return: the updated message dict
        :rtype: dict
        """
        return self._do_produce(model, actor, self._new_data)

    def _do_produce(self, model, actor, target):
        data = json.dumps(model.dump(), sort_keys=True)
        message = {
            'type': type(model).__name__,
            'actor': type(actor).name,
            'topic': model.topic.name,
            'stamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'phase': os.environ.get('LEAPP_CURRENT_PHASE', 'NON-WORKFLOW-EXECUTION'),
            'context': os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'),
            'hostname': os.environ.get('LEAPP_HOSTNAME', socket.getfqdn()),
            'message': {
                'data': data,
                'hash': hashlib.sha256(data.encode('utf-8')).hexdigest()
            }
        }

        if self.stored:
            self._process_message(message.copy())

        target.append(message)
        return message

    def request_answers(self, dialog):
        if dialog.scope in self._answers:
            for key, value in self._answers.get(dialog.scope).items():
                component = dialog.component_by_key(key)
                if component:
                    dialog.answer(component, value)
        return dialog.request_answers(self._dialog_renderer)

    def consume(self, actor, *types):
        """
        Returns all consumable messages and filters them by `types`

        :param types: Variable number of :py:class:`leapp.models.Model` derived types to filter messages to consume
        :param actor: Actor that consumes the data
        :return: Iterable with messages matching the criteria
        """
        messages = list(self._data) + list(self._new_data)
        lookup = dict([(model.__name__, model) for model in type(actor).consumes])
        if types:
            filtered = set(requested.__name__ for requested in types)
            messages = [message for message in messages if message['type'] in filtered]
        return (lookup[message['type']].create(json.loads(message['message']['data'])) for message in messages)
