from leapp.models import Model, fields
from leapp.topics import WorkflowApiTopic


class DepCheck1(Model):
    """ Empty model for test purposes """
    topic = WorkflowApiTopic
