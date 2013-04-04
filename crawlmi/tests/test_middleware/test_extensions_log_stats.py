from twisted.trial import unittest

from crawlmi import signals
from crawlmi.core.signal_manager import SignalManager
from crawlmi.exceptions import NotConfigured
from crawlmi.http.response import Response
from crawlmi.middleware.extensions.log_stats import LogStats
from crawlmi.utils.clock import Clock
from crawlmi.utils.test import get_engine, LogWrapper


class LogStatsTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.engine = get_engine(LOG_STATS_INTERVAL=30)
        self.engine.signals = SignalManager(self.engine)
        self.ls = LogStats(self.engine, clock=self.clock)
        self.lw = LogWrapper()
        self.lw.setUp()

    def tearDown(self):
        self.lw.tearDown()

    def test_config(self):
        self.assertRaises(NotConfigured, LogStats, get_engine(LOG_STATS_INTERVAL=0))

    def test_basic(self):
        # engine is stopped
        self.clock.advance(60)
        self.assertEqual(self.lw.get_first_line(), '')
        # start the engine
        self.engine.signals.send(signals.engine_started)
        self.clock.advance(29)
        self.assertEqual(self.lw.get_first_line(), '')
        self.clock.advance(1)
        self.assertEqual(self.lw.get_first_line(), '[crawlmi] INFO: Crawled 0 pages (at 0 pages/min). Raw speed 0 downloads/min.')
        # download some responses
        self.engine.signals.send(signals.response_downloaded, response=Response(url=''))
        self.engine.signals.send(signals.response_downloaded, response=Response(url=''))
        self.engine.signals.send(signals.response_received, response=Response(url=''))
        self.clock.advance(30)
        self.assertEqual(self.lw.get_first_line(), '[crawlmi] INFO: Crawled 1 pages (at 2 pages/min). Raw speed 4 downloads/min.')
        # stop the engine
        self.engine.signals.send(signals.engine_stopped)
        self.clock.advance(60)
        self.assertEqual(self.lw.get_first_line(), '')
