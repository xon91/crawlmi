from twisted.trial import unittest

from crawlmi.http import Request
from crawlmi.middleware.pipelines.duplicate_filter import DuplicateFilter, clear_duplicate_filter
from crawlmi.utils.test import get_engine


class DuplicateFilterTest(unittest.TestCase):
    def test_process_request(self):
        engine = get_engine()
        mw = DuplicateFilter(engine)

        r1 = Request('http://test.org/1')
        r2 = Request('http://test.org/2')
        r3 = Request('http://test.org/2')

        self.assertIs(mw.process_request(r1), r1)
        self.assertIs(mw.process_request(r2), r2)
        self.assertIsNone(mw.process_request(r3))

        engine.signals.send(clear_duplicate_filter)
        self.assertIs(mw.process_request(r3), r3)

    def test_tags(self):
        engine = get_engine()
        mw = DuplicateFilter(engine)

        r1 = Request('http://test.org/', meta={'df_tag': '1'})
        r2 = Request('http://test.org/', meta={'df_tag': '2'})
        r3 = Request('http://test.org/', meta={'df_tag': '2'})

        self.assertIs(mw.process_request(r1), r1)
        self.assertIs(mw.process_request(r2), r2)
        self.assertIsNone(mw.process_request(r3))

        engine.signals.send(clear_duplicate_filter, df_tag='2')

        self.assertIsNone(mw.process_request(r1))
        self.assertIs(mw.process_request(r2), r2)
        self.assertIsNone(mw.process_request(r3))
