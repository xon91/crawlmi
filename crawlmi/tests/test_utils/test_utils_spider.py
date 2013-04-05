from twisted.trial import unittest

from crawlmi.spider import BaseSpider
from crawlmi.utils.spider import iter_spider_classes


class MyBaseSpider(BaseSpider):
    pass # abstract spider


class MySpider1(MyBaseSpider):
    name = 'myspider1'


class MySpider2(MyBaseSpider):
    name = 'myspider2'


class UtilsSpiderTest(unittest.TestCase):
    def test_iter_spider_classes(self):
        import crawlmi.tests.test_utils.test_utils_spider
        it = iter_spider_classes(crawlmi.tests.test_utils.test_utils_spider)
        self.assertSetEqual(set(it), set([MySpider1, MySpider2]))
