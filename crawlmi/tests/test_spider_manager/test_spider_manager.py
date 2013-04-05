import os
import shutil
import sys

from twisted.trial import unittest

from crawlmi.settings import Settings
from crawlmi.spider.spider_manager import SpiderManager
from crawlmi.utils.test import LogWrapper


module_dir = os.path.dirname(os.path.abspath(__file__))


class SpiderManagerTest(unittest.TestCase):
    def setUp(self):
        orig_spiders_dir = os.path.join(module_dir, 'test_spiders')
        self.tmpdir = self.mktemp()
        os.mkdir(self.tmpdir)
        self.spiders_dir = os.path.join(self.tmpdir, 'test_spiders_xxx')
        shutil.copytree(orig_spiders_dir, self.spiders_dir)
        sys.path.append(self.tmpdir)

        settings = {'SPIDER_MODULES': ['test_spiders_xxx']}
        self.manager = SpiderManager(Settings(settings))
        self.lw = LogWrapper()
        self.lw.setUp()

    def tearDown(self):
        sys.path.remove(self.tmpdir)
        self.lw.tearDown()

    def test_get_spiders(self):
        self.assertSetEqual(
            set(self.manager.get_spiders()),
            set(['spider1', 'spider2', 'spider3']))

    def test_create_by_name(self):
        spider1 = self.manager.create_spider_by_name('spider1')
        self.assertEqual(spider1.__class__.__name__, 'Spider1')
        spider2 = self.manager.create_spider_by_name('spider2')
        self.assertEqual(spider2.__class__.__name__, 'Spider2')

    def test_get_spiders_by_url(self):
        self.assertEqual(self.manager.get_spiders_by_url('http://crawlmi1.org/test'), ['spider1'])
        self.assertEqual(self.manager.get_spiders_by_url('http://crawlmi2.org/test'), ['spider2'])
        self.assertEqual(set(self.manager.get_spiders_by_url('http://crawlmi3.org/test')), set(['spider1', 'spider2']))
        self.assertEqual(self.manager.get_spiders_by_url('http://crawlmi999.org/test'), [])
        self.assertEqual(self.manager.get_spiders_by_url('http://spider3.com'), ['spider3'])

    def test_create_spiders_by_url(self):
        spider = self.manager.create_spider_by_url('http://crawlmi1.org/test')
        self.assertEqual(spider.__class__.__name__, 'Spider1')

        spider = self.manager.create_spider_by_url('http://crawlmi3.org/test')
        self.assertIsNone(spider)
        self.assertTrue(self.lw.get_first_line().startswith('[crawlmi] ERROR: More than one spider can handle:'))

        spider = self.manager.create_spider_by_url('http://crawlmi999.org/test')
        self.assertIsNone(spider)
        self.assertTrue(self.lw.get_first_line().startswith('[crawlmi] ERROR: Unable to find spider that handles:'))

    def test_load_spider_module(self):
        settings = {'SPIDER_MODULES': ['crawlmi.tests.test_spider_manager.test_spiders.spider1']}
        self.manager = SpiderManager(Settings(settings))
        self.assertEqual(len(self.manager._spiders), 1)

    def test_load_base_spider(self):
        settings = {'SPIDER_MODULES': ['crawlmi.tests.test_spider_manager.test_spiders.spider0']}
        self.manager = SpiderManager(Settings(settings))
        self.assertEqual(len(self.manager._spiders), 0)
