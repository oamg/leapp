from leapp.models import Model, fields
from leapp.topics import ConfigTopic


class UnitTestConfig(Model):
    topic = ConfigTopic
    value = fields.String(default='unit-test')
