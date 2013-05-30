import pprint

from .statistics import Statistics
from .top_samples import TopSamples
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

    def add_value(self, key, value, weight=1.0):
        statistics = self._stats.get(key)
        if statistics is None:
            statistics = self._stats[key] = Statistics()
        elif not isinstance(statistics, Statistics):
            raise RuntimeError('Object with key %s is not of type Statistics' % key)
        statistics.add_value(value, weight)

    def add_sample(self, key, priority, value):
        top_samples = self._stats.get(key)
        if top_samples is None:
            top_samples = self._stats[key] = TopSamples()
        elif not isinstance(top_samples, TopSamples):
            raise RuntimeError('Object with key %s is not of type TopSamples' % key)
        top_samples.add_sample(priority, value)

    def clear_stats(self):
        self._stats.clear()

    def dump_stats(self):
        if self._dump:
            log.msg('Dumping crawlmi stats:\n' + pprint.pformat(self._stats))
