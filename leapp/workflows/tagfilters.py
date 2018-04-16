from leapp.exceptions import TagFilterUsageError
from leapp.tags import Tag


class TagFilter(object):
    def __init__(self, phase, *tags):
        self.phase = phase
        self.tags = tags
        if not self.phase or not isinstance(self.phase, type) or not issubclass(self.phase, Tag):
            raise TagFilterUsageError("TagFilter phase key needs to be set to a tag.")

    def get_before(self):
        result = set(actor for actor in self.phase.Before.actors)
        [result.intersection_update(tag.actors) for tag in self.tags]
        result.update(self.phase.Before.Common.actors)
        return tuple(result)

    def get_after(self):
        result = set(actor for actor in self.phase.After.actors)
        [result.intersection_update(tag.actors) for tag in self.tags]
        result.update(self.phase.After.Common.actors)
        return tuple(result)

    def get(self):
        result = set(actor for actor in self.phase.actors)
        [result.intersection_update(tag.actors) for tag in self.tags]
        result.update(self.phase.Common.actors)
        return tuple(result)
