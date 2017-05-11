class Actor(object):
    def __init__(self, *args, **kwargs):
        self._driver = kwargs.pop('driver')

    @property
    def driver(self):
        return self._driver

    def discover(self):
        pass

    def configure(self):
        pass

    def execute(self):
        pass
