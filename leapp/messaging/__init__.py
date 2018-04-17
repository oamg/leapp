import json
import os
import socket


class BaseMessaging(object):
    """
    BaseMessaging is the Base class for all messaging implementations - It provides the basic interface that is
    supported within the framework - That are the `produce` and `consume` methods.
    """
    def __init__(self):
        self._data = []
        self._new_data = []

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

    def produce(self, message):
        """
        Called to send a message to be available for other actors.

        Extends message with the following fields:
        - :field str phase: Environment variable LEAPP_CURRENT_PHASE or value 'NON-WORKFLOW-EXECUTION'
        - :field str context: Environment variable LEAPP_EXECUTION_ID or value 'TESTING-CONTEXT'
        - :field str hostname: Hostname of the system either via env LEAPP_HOSTNAME or `socket.getfqdn()`

        :param message: Dictionary of message items with the following fields:
            - :field str actor: Who produced the message
            - :field str topic: Name of the topic of the message
            - :field str type: Model class name
            - :field str stamp: UTC Timestamp in ISO format
            - :field dict message:
                - :field str data: JSON dump string with sorted keys
                - :field str hash: SHA256 hex digest hash of `data`
        :type message: dict
        :return: the updated message dict
        :rtype: dict
        """
        message.setdefault('phase', os.environ.get('LEAPP_CURRENT_PHASE', 'NON-WORKFLOW-EXECUTION'))
        message.setdefault('context', os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'))
        message.setdefault('hostname', os.environ.get('LEAPP_HOSTNAME', socket.getfqdn()))
        self._new_data.append(message)

        return self._process_message(message)

    def consume(self, *types):
        """
        Returns all consumable messages and filters them by `types`

        :param types: Variable number of :py:class:`leapp.models.Model` derived types to filter messages to consume
        :return: Iterable with messages matching the criteria
        """
        if not type:
            return self._data + self._new_data
        lookup = dict([(model.__name__, model) for model in types])
        return (lookup[message['type']].create(json.loads(message['message']['data']))
                for message in (self._data + self._new_data) if message['type'] in lookup)
