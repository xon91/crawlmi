from twisted.internet.error import (TimeoutError as ServerTimeoutError,
    DNSLookupError, ConnectionRefusedError, ConnectionDone, ConnectError,
    ConnectionLost)
from twisted.python.failure import Failure
from twisted.trial import unittest

from crawlmi.http import Request, Response
from crawlmi.middleware.pipelines.retry import Retry
from crawlmi.utils.test import get_engine


class RetryTest(unittest.TestCase):
    def setUp(self):
        engine = get_engine()
        self.mw = Retry(engine)
        self.mw.max_retry_times = 2

    def test_priority_adjust(self):
        req = Request('http://www.scrapytest.org/503')
        rsp = Response('http://www.scrapytest.org/503', body='', status=503, request=req)
        req2 = self.mw.process_response(rsp)
        self.assertTrue(req2.priority < req.priority)

    def test_404(self):
        req = Request('http://www.scrapytest.org/404')
        rsp = Response('http://www.scrapytest.org/404', body='', status=404, request=req)
        self.assertIs(self.mw.process_response(rsp), rsp)

    def test_503(self):
        req = Request('http://www.scrapytest.org/503')
        rsp = Response('http://www.scrapytest.org/503', body='', status=503, request=req)

        # first retry
        req = self.mw.process_response(rsp)
        self.assertIsInstance(req, Request)
        self.assertEqual(req.meta['retry_times'], 1)

        # second retry
        rsp.request = req
        req = self.mw.process_response(rsp)
        self.assertIsInstance(req, Request)
        self.assertEqual(req.meta['retry_times'], 2)

        # discard it
        rsp.request = req
        self.assertIs(self.mw.process_response(rsp), rsp)

    def test_twisted_errors(self):
        for exc in (ServerTimeoutError, DNSLookupError, ConnectionRefusedError,
                    ConnectionDone, ConnectError, ConnectionLost):
            req = Request('http://www.test.org/%s' % exc.__name__)
            self._test_retry_exception(req, exc())

    def _test_retry_exception(self, req, exception):
        failure = Failure(exception)

        # first retry
        failure.request = req
        req = self.mw.process_failure(failure)
        self.assertIsInstance(req, Request)
        self.assertEqual(req.meta['retry_times'], 1)

        # second retry
        failure.request = req
        req = self.mw.process_failure(failure)
        self.assertIsInstance(req, Request)
        self.assertEqual(req.meta['retry_times'], 2)

        # discard it
        failure.request = req
        req = self.mw.process_failure(failure)
        self.assertIs(req, failure)
