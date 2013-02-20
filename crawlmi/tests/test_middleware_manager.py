from twisted.trial import unittest

from crawlmi.exceptions import NotConfigured
from crawlmi.middleware.middleware_manager import MiddlewareManager
from crawlmi.utils.test import get_engine, LogWrapper


class M1(object):
    def __init__(self, engine):
        pass


class M2(object):
    def __init__(self, engine):
        pass


class MOff(object):
    def __init__(self, engine):
        raise NotConfigured


class TestMiddlewareManager(MiddlewareManager):
    def _get_mwlist(self):
        return ['crawlmi.tests.test_middleware_manager.%s' % x
                for x in ['M1', 'MOff', 'M2']]


class MiddlewareManagerTest(unittest.TestCase):
    def setUp(self):
        self.lw = LogWrapper()
        self.lw.setUp()

    def tearDown(self):
        self.lw.tearDown()

    def test_init(self):
        mw = TestMiddlewareManager(get_engine())
        active = [x.__class__ for x in mw.middlewares]
        self.assertListEqual(active, [M1, M2])

        logged = self.lw.get_first_line()
        self.assertEqual(logged, "[crawlmi] WARNING: Disabled <class 'crawlmi.tests.test_middleware_manager.MOff'>:")

    def test_init2(self):
        mw = TestMiddlewareManager(get_engine(), mw_classes=[M1, M2, MOff])
        active = [x.__class__ for x in mw.middlewares]
        self.assertListEqual(active, [M1, M2])
