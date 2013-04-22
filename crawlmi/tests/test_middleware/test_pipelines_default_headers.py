from twisted.trial import unittest

from crawlmi.http import Request
from crawlmi.middleware.pipelines.default_headers import DefaultHeaders
from crawlmi.utils.test import get_engine


class DefaultHeadersTest(unittest.TestCase):
    def setUp(self):
        self.dh = DefaultHeaders(get_engine())
        self.defaults = {}
        for k, v in self.dh.headers.iteritems():
            self.defaults[k] = [v]

    def test_process_request(self):
        req = Request('http://github.com/')
        req = self.dh.process_request(req)
        self.assertDictEqual(req.headers, self.defaults)

    def test_update_headers(self):
        headers = {'Accept-Language': ['es'], 'Test-Header': ['test']}
        req = Request('http://github.com/', headers=headers)
        self.assertDictEqual(req.headers, headers)
        req = self.dh.process_request(req)
        self.defaults.update(headers)
        self.assertDictEqual(req.headers, self.defaults)
