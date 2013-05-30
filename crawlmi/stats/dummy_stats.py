class DummyStats(object):

    def __init__(self, engine):
        pass

    def get_value(self, key, default=None):
        return default

    def get_stats(self):
        return {}

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

    def add_value(self, key, value, weight=1.0):
        pass

    def add_sample(self, key, priority, value):
        pass

    def clear_stats(self):
        pass

    def dump_stats(self):
        pass
