import unittest2

from crawlmi.exceptions import NotConfigured
from crawlmi.middleware.middleware_manager import MiddlewareManager
from crawlmi.utils.test import get_engine


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


class MiddlewareManagerTest(unittest2.TestCase):
    def test_init(self):
        mw = TestMiddlewareManager(get_engine())
        active = [x.__class__ for x in mw.middlewares]
        self.assertListEqual(active, [M1, M2])
