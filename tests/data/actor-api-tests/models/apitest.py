from leapp.models import Model, fields
from leapp.topics import ApiTestTopic


class ApiTest(Model):
    topic = ApiTestTopic

    data = fields.String()


class ApiTestProduce(ApiTest):
    pass


class ApiTestConsume(ApiTest):
    pass
