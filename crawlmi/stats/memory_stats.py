import pprint

from crawlmi import log


class MemoryStats(object):

    def __init__(self, engine):
        self._stats = {}
        self._dump = engine.settings.get_bool('STATS_DUMP')

    def get_value(self, key, default=None):
        return self._stats.get(key, default)

    def get_stats(self):
        return self._stats

    def set_value(self, key, value):
        self._stats[key] = value

    def set_stats(self, stats):
        self._stats = stats

    def inc_value(self, key, count=1, start=0):
        d = self._stats
        d[key] = d.setdefault(key, start) + count

    def max_value(self, key, value):
        self._stats[key] = max(self._stats.setdefault(key, value), value)

    def min_value(self, key, value):
        self._stats[key] = min(self._stats.setdefault(key, value), value)

    def clear_stats(self):
        self._stats.clear()

    def dump_stats(self):
        if self._dump:
            log.msg('Dumping crawlmi stats:\n' + pprint.pformat(self._stats))
