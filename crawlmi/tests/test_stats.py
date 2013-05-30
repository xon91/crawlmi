from twisted.trial import unittest

from crawlmi.stats import DummyStats, MemoryStats
from crawlmi.utils.test import get_engine, LogWrapper, eq


class StatsTest(unittest.TestCase):

    def setUp(self):
        self.lw = LogWrapper()
        self.lw.setUp()

    def tearDown(self):
        self.lw.tearDown()

    def test_memory_stats(self):
        stats = MemoryStats(get_engine(STATS_DUMP=True))
        self.assertEqual(stats.get_stats(), {})
        self.assertEqual(stats.get_value('anything'), None)
        self.assertEqual(stats.get_value('anything', 'default'), 'default')
        stats.set_value('test', 'value')
        self.assertEqual(stats.get_stats(), {'test': 'value'})
        stats.set_value('test2', 23)
        self.assertEqual(stats.get_stats(), {'test': 'value', 'test2': 23})
        self.assertEqual(stats.get_value('test2'), 23)
        stats.inc_value('test2')
        self.assertEqual(stats.get_value('test2'), 24)
        stats.inc_value('test2', 6)
        self.assertEqual(stats.get_value('test2'), 30)
        stats.max_value('test2', 6)
        self.assertEqual(stats.get_value('test2'), 30)
        stats.max_value('test2', 40)
        self.assertEqual(stats.get_value('test2'), 40)
        stats.max_value('test3', 1)
        self.assertEqual(stats.get_value('test3'), 1)
        stats.min_value('test2', 60)
        self.assertEqual(stats.get_value('test2'), 40)
        stats.min_value('test2', 35)
        self.assertEqual(stats.get_value('test2'), 35)
        stats.min_value('test4', 7)
        self.assertEqual(stats.get_value('test4'), 7)

        stats.add_value('stats', 3)
        stats.add_value('stats', 2, 2.0)
        statistics = stats.get_value('stats')
        self.assertTrue(eq(statistics.average, 7.0/3.0), statistics.average)
        self.assertRaises(RuntimeError, stats.add_value, 'test4', 1)

        stats.add_sample('samples', 3, 'hello')
        stats.add_sample('samples', 2, 'world')
        samples = stats.get_value('samples')
        self.assertEqual(len(samples), 2)
        self.assertListEqual(samples.samples, [(3, 'hello'), (2, 'world')])
        self.assertRaises(RuntimeError, stats.add_value, 'test4', 5, '!')

        stats.dump_stats()
        logged = self.lw.get_first_line(clear=False)
        self.assertTrue(logged.startswith('[crawlmi] INFO: Dumping crawlmi stats:'))
        logged = self.lw.get_logged()
        self.assertIn('test', logged)
        self.assertIn('test2', logged)
        self.assertIn('test3', logged)
        self.assertIn('test3', logged)
        self.assertIn('stats', logged)
        self.assertIn('samples', logged)

    def test_dummy_stats(self):
        stats = DummyStats(get_engine())
        self.assertEqual(stats.get_stats(), {})
        self.assertEqual(stats.get_value('anything'), None)
        self.assertEqual(stats.get_value('anything', 'default'), 'default')
        stats.set_value('test', 'value')
        stats.inc_value('v1')
        stats.max_value('v2', 100)
        stats.min_value('v3', 100)
        stats.set_value('test', 'value')
        stats.add_value('stats', 100)
        stats.add_value('stats', 100, 12)
        stats.add_sample('samples', 3, 'hello')
        self.assertEqual(stats.get_stats(), {})
        stats.dump_stats()
