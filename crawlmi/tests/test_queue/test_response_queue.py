from twisted.trial import unittest

from crawlmi.http import Response
from crawlmi.queue import ResponseQueue


class ResponseQueueTest(unittest.TestCase):
    def test_limit(self):
        q = ResponseQueue(10)
        r1 = Response('', body='x' * 5)
        r2 = Response('', body='y' * 5)

        self.assertFalse(q.needs_backout())
        q.push(r1)
        self.assertFalse(q.needs_backout())
        q.push(r2)
        self.assertTrue(q.needs_backout())
        q.pop()
        self.assertFalse(q.needs_backout())

    def test_no_limit(self):
        q = ResponseQueue(0)
        r1 = Response('', body='x' * 50)
        r2 = Response('', body='y' * 50)

        self.assertFalse(q.needs_backout())
        q.push(r1)
        q.push(r2)
        self.assertFalse(q.needs_backout())
