import datetime
import hashlib
import json
import multiprocessing
import os
import socket


class BaseMessaging(object):
    """
    BaseMessaging is the Base class for all messaging implementations - It provides the basic interface that is
    supported within the framework - That are the `produce` and `consume` methods.
    """
    def __init__(self, stored=True):
        self._manager = multiprocessing.Manager()
        self._data = self._manager.list()
        self._new_data = self._manager.list()
        self._stored = stored

    @property
    def stored(self):
        """
        :return: If the messages are stored immediately this returns True otherwise False
        """
        return self._stored

    def get_new(self):
        """
        Get all newly produced messages
        :return: List of newly processed messages
        """
        return list(self._new_data)

    def store(self):
        """
        Stores messages that have been produced but not stored - Noop if stored is True
        :return: None
        """
        if not self.stored:
            for message in self._new_data:
                self._process_message(message)

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
        """
        self._perform_load(consumes)

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
                'hash': hashlib.sha256(data).hexdigest()
            }
        }
        self._new_data.append(message)
        if self.stored:
            return self._process_message(message)
        else:
            return message

    def consume(self, *types):
        """
        Returns all consumable messages and filters them by `types`

        :param types: Variable number of :py:class:`leapp.models.Model` derived types to filter messages to consume
        :return: Iterable with messages matching the criteria
        """
        all_messages = list(self._data) + list(self._new_data)
        if not type:
            return all_messages
        lookup = dict([(model.__name__, model) for model in types])
        return (lookup[message['type']].create(json.loads(message['message']['data']))
                for message in all_messages if message['type'] in lookup)
