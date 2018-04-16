import json
import os
import socket


class BaseMessaging(object):
    def __init__(self):
        self._data = []
        self._new_data = []

    def produce(self, topic, message):
        message.setdefault('topic', topic)
        message.setdefault('phase', os.environ.get('LEAPP_CURRENT_PHASE', 'NON-WORKFLOW-EXECUTION'))
        message.setdefault('context', os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'))
        message.setdefault('hostname', os.environ.get('LEAPP_HOSTNAME', socket.getfqdn()))
        self._new_data.append(message)
        return message

    def consume(self, *types):
        if not type:
            return self._data + self._new_data
        lookup = dict([(model.__name__, model) for model in types])
        return (lookup[message['type']].create(json.loads(message['message']['data']))
                for message in (self._data + self._new_data) if message['type'] in lookup)
