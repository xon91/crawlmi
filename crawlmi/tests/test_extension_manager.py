import unittest2

from crawlmi.exceptions import NotConfigured
from crawlmi.middleware.extension_manager import ExtensionManager
from crawlmi.utils.test import get_engine


class E1(object):
    name = 'e1'

    def __init__(self, engine):
        pass

class E2(object):
    def __init__(self, engine):
        pass


class EOff(object):
    name = 'eoff'

    def __init__(self, engine):
        raise NotConfigured


class ExtensionManagerTest(unittest2.TestCase):
    def test_basic(self):
        extensions = dict(('crawlmi.tests.test_extension_manager.%s' % x, 0)
                          for x in ['E1', 'E2', 'EOff'])
        engine = get_engine(EXTENSIONS_BASE=extensions)
        em = ExtensionManager(engine)

        active = [x.__class__ for x in em.middlewares]
        self.assertListEqual(active, [E1, E2])
        self.assertIsInstance(em['e1'], E1)
        self.assertRaises(KeyError, em.__getitem__, 'eoff')
