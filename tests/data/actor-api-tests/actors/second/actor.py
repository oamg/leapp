from leapp.actors import Actor
from leapp.tags import ActorFileApiTag
from leapp.models import ApiTestConsume, ApiTestProduce


class Second(Actor):
    name = 'second'
    description = 'No description has been provided for the second actor.'
    consumes = (ApiTestConsume,)
    produces = (ApiTestProduce,)
    tags = (ActorFileApiTag,)

    def process(self):
        pass
