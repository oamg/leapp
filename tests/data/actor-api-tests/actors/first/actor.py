from leapp.actors import Actor
from leapp.tags import ActorFileApiTag
from leapp.models import ApiTestConsume, ApiTestProduce


class First(Actor):
    name = 'first'
    description = 'No description has been provided for the first actor.'
    consumes = (ApiTestConsume,)
    produces = (ApiTestProduce,)
    tags = (ActorFileApiTag,)

    def process(self):
        pass
