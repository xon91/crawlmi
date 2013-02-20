from twisted.trial import unittest

from crawlmi.stats import DummyStats, MemoryStats
from crawlmi.utils.test import get_engine, LogWrapper


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

        stats.dump_stats()
        logged = self.lw.get_first_line(clear=False)
        self.assertTrue(logged.startswith('[crawlmi] INFO: Dumping crawlmi stats:'))
        logged = self.lw.get_logged()
        self.assertIn('test', logged)
        self.assertIn('test2', logged)
        self.assertIn('test3', logged)
        self.assertIn('test3', logged)

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
        self.assertEqual(stats.get_stats(), {})
        stats.dump_stats()
