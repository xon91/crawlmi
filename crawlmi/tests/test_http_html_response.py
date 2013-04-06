from twisted.trial import unittest

from crawlmi.http import HtmlResponse
from crawlmi.parser.selectors import HtmlXPathSelector


class HtmlResponseTest(unittest.TestCase):
    def setUp(self):
        self.resp = HtmlResponse('http://github.com/', body='''<head>
        <base href="http://www.w3schools.com/" target="_blank"></head>
        <body></body>''')

    def test_selector(self):
        self.assertIsInstance(self.resp.selector, HtmlXPathSelector)

    def test_base_url(self):
        self.assertEqual(self.resp.base_url, 'http://www.w3schools.com/')
