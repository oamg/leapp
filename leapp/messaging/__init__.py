import json
import multiprocessing
import os
import socket

from leapp.snactor.utils import get_project_metadata, find_project_basedir
from leapp.utils.actorapi import get_actor_api
from leapp.utils.audit import Audit, Message, MessageData, get_messages


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
        lookup = {model.__name__: model for model in types}
        return (lookup[message['type']].create(json.loads(message['message']['data']))
                for message in (self._data + self._new_data) if message['type'] in lookup)


class InProcessMessaging(BaseMessaging):
    def __init__(self):
        super(InProcessMessaging, self).__init__()

    def load(self, consumes):
        names = [consume.__name__ for consume in consumes]
        self._data = Message.get_all(names)

    def produce(self, topic, message):
        message = super(InProcessMessaging, self).produce(topic, message)
        message['event'] = 'new-message'
        message_keys = ('stamp', 'topic', 'actor', 'phase', 'hostname', 'context', 'msg_type')
        audit_keys = ('event', 'stamp', 'data', 'actor', 'phase', 'hostname', 'context')
        message['msg_type'] = message.pop('type')
        payload = message.pop('message')
        msg = Message(**dict(((k, message[k]) for k in message_keys if k in message)))
        audit = Audit(**dict(((k, message[k]) for k in audit_keys if k in message)))
        audit.message = msg
        audit.message.data = MessageData(data=payload['data'], hash_id=payload['hash'])
        audit.store()
        return message

    def load(self, consumes):
        context = os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT')
        self._data = get_messages([consume.__name__ for consume in consumes], context)


class RemoteMessaging(BaseMessaging):
    def __init__(self):
        super(RemoteMessaging, self).__init__()
        self._session = get_actor_api()

    def produce(self, topic, message):
        message = super(RemoteMessaging, self).produce(topic, message)
        self._session.post('leapp://localhost/actors/v1/message', json=message)
        return message

    def load(self, consumes):
        names = [consume.__name__ for consume in consumes]
        request = self._session.post('leapp://localhost/actors/v1/messages', json={
            'context': os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'),
            'messages': names})
        request.raise_for_status()
        self._data = request.json()['messages']


class ProjectLocalMessaging(BaseMessaging):
    def __init__(self):
        super(ProjectLocalMessaging, self).__init__()
        self._manager = multiprocessing.Manager()
        self._data = self._manager.list()
        self._new_data = self._manager.list()

    def load(self):
        self._data = self._manager.list(get_project_metadata(find_project_basedir('.'))['messages'])

    def get_new(self):
        return list(self._new_data)

    def store(self):
        self._data.extend(self._new_data)
        metadata = get_project_metadata(find_project_basedir('.'))
        metadata.update({'messages': list(self._data)})
        with open(os.path.join(find_project_basedir('.'), '.leapp/info'), 'w') as f:
            json.dump(metadata, f, indent=2)
