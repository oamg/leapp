from leapp.models import Model, fields
from leapp.topics import DeprecationTopic
from leapp.utils.deprecation import deprecated


@deprecated('2010-01-01', 'This model is deprecated - Please do not use it anymore')
class DeprecatedModel(Model):
    topic = DeprecationTopic


@deprecated('2010-01-01', 'This model is deprecated - This should not be warned about')
class SuppressedDeprecatedModel(Model):
    topic = DeprecationTopic
