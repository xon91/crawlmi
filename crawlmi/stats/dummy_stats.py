class DummyStats(object):

    def __init__(self):
        self._stats = {}

    def get_value(self, key, default=None):
        return default

    def get_stats(self):
        return self._stats

    def set_value(self, key, value):
        pass

    def set_stats(self, stats):
        pass

    def inc_value(self, key, count=1, start=0):
        pass

    def max_value(self, key, value):
        pass

    def min_value(self, key, value):
        pass

    def clear_stats(self):
        self._stats.clear()
