
from leapp.messaging import BaseMessaging


class TestMessaging(BaseMessaging):
    """
    This class implements a messaging implementation made for unit tests - Data is only stored in memory and
    not stored in a database.
    """

    def __init__(self, config_model=None):
        super(TestMessaging, self).__init__(stored=False, config_model=config_model)

    def feed(self, *messages):
        self._data.extend([message.dump() for message in messages])

    def _process_message(self, message):
        return message

    def _perform_load(self, consumes):
        pass
