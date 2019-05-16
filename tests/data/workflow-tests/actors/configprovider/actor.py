from leapp.actors import Actor
from leapp.models import UnitTestConfig
from leapp.tags import UnitTestWorkflowTag


class ConfigProvider(Actor):
    """
    No documentation has been provided for the config_provider actor.
    """

    name = 'config_provider'
    consumes = ()
    produces = (UnitTestConfig,)
    tags = (UnitTestWorkflowTag,)

    def process(self):
        self.produce(UnitTestConfig())
