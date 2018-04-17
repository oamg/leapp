import os

from leapp.messaging import BaseMessaging
from leapp.utils.actorapi import get_actor_api


class RemoteMessaging(BaseMessaging):
    """
    This class implements the messaging over a remote API via HTTP over an UNIX domain socket.
    """

    def __init__(self):
        super(RemoteMessaging, self).__init__()
        self._session = get_actor_api()

    def _process_message(self, message):
        self._session.post('leapp://localhost/actors/v1/message', json=message)
        return message

    def _perform_load(self, consumes):
        names = [consume.__name__ for consume in consumes]
        request = self._session.post('leapp://localhost/actors/v1/messages', json={
            'context': os.environ.get('LEAPP_EXECUTION_ID', 'TESTING-CONTEXT'),
            'messages': names})
        request.raise_for_status()
        self._data = request.json()['messages']