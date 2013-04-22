from twisted.trial import unittest

from crawlmi.http import Request, Response, TextResponse
from crawlmi.middleware.pipelines.filter import Filter
from crawlmi.utils.test import get_engine


class FilterUrlLengthTest(unittest.TestCase):
    def _get_engine(self, **kwargs):
        engine = get_engine(**kwargs)
        self.stats = engine.stats
        return engine

    def test_nontext_response(self):
        mw = Filter(self._get_engine(FILTER_NONTEXT_RESPONSE=True))
        req = Request('http://github.com/')

        good1 = TextResponse('', request=req)
        good2 = mw.process_response(good1)
        self.assertIs(good1, good2)

        bad1 = Response('', request=req)
        bad2 = mw.process_response(bad1)
        self.assertIsNone(bad2)

        mw = Filter(self._get_engine(FILTER_NONTEXT_RESPONSE=False))
        bad3 = mw.process_response(bad1)
        self.assertIs(bad1, bad3)

    def test_url_length_limit(self):
        mw = Filter(self._get_engine(FILTER_URL_LENGTH_LIMIT=11))

        good1 = Request('http://a.b/')
        good2 = mw.process_request(good1)
        self.assertIs(good1, good2)

        bad1 = Request('http://a.bc/')
        bad2 = mw.process_request(bad1)
        self.assertIsNone(bad2)

    def test_filter_non_200(self):
        mw = Filter(self._get_engine(FILTER_NON_200_RESPONSE_STATUS=True))
        req = Request('http://github.com/')

        good1 = Response('', request=req, status=200)
        good2 = mw.process_response(good1)
        self.assertIs(good1, good2)

        bad1 = Response('', request=req, status=404)
        bad2 = mw.process_response(bad1)
        self.assertIsNone(bad2)

        mw = Filter(self._get_engine(FILTER_NON_200_RESPONSE_STATUS=False))
        bad3 = mw.process_response(bad1)
        self.assertIs(bad1, bad3)

    def test_response_status(self):
        mw = Filter(self._get_engine(FILTER_RESPONSE_STATUS=lambda x: x != 201))
        req = Request('http://github.com/')

        good1 = Response('', request=req, status=201)
        good2 = mw.process_response(good1)
        self.assertIs(good1, good2)

        bad1 = Response('', request=req, status=200)
        bad2 = mw.process_response(bad1)
        self.assertIsNone(bad2)
