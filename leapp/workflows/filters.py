import itertools

from leapp.workflows.tagfilters import TagFilter


class Filter(object):
    def __init__(self, *args):
        self.filters = args

    def _get_with(self, fun):
        return tuple(itertools.chain(*(fun(f) for f in self.filters)))

    def get_before(self):
        return self._get_with(TagFilter.get_before)

    def get_after(self):
        return self._get_with(TagFilter.get_after)

    def get(self):
        return self._get_with(TagFilter.get)
