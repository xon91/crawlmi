from twisted.python.failure import Failure
from twisted.trial import unittest

from crawlmi.http import Request, Response
from crawlmi.middleware.pipelines.downloader_stats import DownloaderStats
from crawlmi.utils.test import get_engine


class DownloaderStatsTest(unittest.TestCase):
    def setUp(self):
        engine = get_engine()
        self.stats = engine.stats
        self.mw = DownloaderStats(engine)

        self.req = Request('http://github.com')
        self.resp = Response('scrapytest.org', status=400, request=self.req)

    def test_process_request(self):
        req2 = self.mw.process_request(self.req)
        self.assertIs(req2, self.req)
        self.assertEqual(self.stats.get_value('downloader/request_count'), 1)
        self.assertEqual(self.stats.get_value('downloader/request_method_count/GET'), 1)
        self.assertGreater(self.stats.get_value('downloader/request_bytes'), 0)

    def test_process_response(self):
        resp2 = self.mw.process_response(self.resp)
        self.assertIs(resp2, self.resp)
        self.assertEqual(self.stats.get_value('downloader/response_count'), 1)
        self.assertEqual(self.stats.get_value('downloader/response_status_count/400'), 1)
        self.assertGreater(self.stats.get_value('downloader/response_bytes'), 0)

    def test_process_failure(self):
        failure = Failure(ValueError())
        failure2 = self.mw.process_failure(failure)
        self.assertIs(failure, failure2)
        self.assertEqual(self.stats.get_value('downloader/exception_count'), 1)
        self.assertEqual(self.stats.get_value('downloader/exception_type_count/exceptions.ValueError'), 1)
