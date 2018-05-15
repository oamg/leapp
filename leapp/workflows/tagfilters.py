from leapp.exceptions import TagFilterUsageError
from leapp.tags import Tag


class TagFilter(object):
    def __init__(self, phase, *tags):
        if not phase or not isinstance(phase, type) or not issubclass(phase, Tag):
            raise TagFilterUsageError("TagFilter phase parameter needs to be set to a tag.")
        self.phase = phase
        self.tags = tags

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
