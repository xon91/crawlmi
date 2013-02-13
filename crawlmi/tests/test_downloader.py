import unittest2

from twisted.internet import defer, task
from twisted.python.failure import Failure

from crawlmi.core.downloader import Slot
from crawlmi.http.request import Request


class MockDownloaderHandler(object):
    def __init__(self):
        self.dfds = {}

    def download_request(self, request):
        dfd = defer.Deferred()
        self.dfds[request] = dfd
        return dfd


class DownloaderSlotTest(unittest2.TestCase):
    default_concurrency = 2
    default_delay = 0
    default_randomize_delay = False

    def setUp(self):
        self.handler = MockDownloaderHandler()
        self.slot = Slot(self.handler, self.default_concurrency,
                         self.default_delay, self.default_randomize_delay)
        self.clock = task.Clock()
        self.slot.processing._clock = self.clock

    def _get_request(self, id, func=None):
        dfd = defer.Deferred()
        if func:
            dfd.addBoth(func)
        return (Request('http://www.github.com/%s/' % id), dfd)

    def _call_deferred(self, request, response):
        self.handler.dfds[request].callback(response)

    def _fail_deferred(self, request, error):
        self.handler.dfds[request].errback(Failure(error))

    def test_basic(self):
        received = []
        def downloaded(result):
            received.append(result)

        # enqueue 3 requests
        r1, dfd1 = self._get_request('1', downloaded)
        self.slot.enqueue(r1, dfd1)
        self.assertEqual(len(self.slot.in_progress), 1)
        self.assertEqual(len(self.slot.transferring), 0)
        r2, dfd2 = self._get_request('2', downloaded)
        r3, dfd3 = self._get_request('3', downloaded)
        self.slot.enqueue(r2, dfd2)
        self.slot.enqueue(r3, dfd3)
        self.assertEqual(len(self.slot.in_progress), 3)
        self.assertEqual(self.slot.free_slots, 2)

        # make 2 requests being downloaded
        self.clock.advance(0)
        self.assertEqual(len(self.slot.transferring), 2)
        self.assertEqual(len(self.slot.in_progress), 3)
        self.assertEqual(self.slot.free_slots, 0)

        # download 2nd request
        self._call_deferred(r2, r2)
        self.assertIs(received[-1], r2)
        self.assertEqual(len(self.slot.transferring), 1)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(self.slot.free_slots, 1)

        # make the last request being downloaded
        self.clock.advance(0)
        self.assertEqual(self.slot.free_slots, 0)

        # download the rest of the requests
        self._call_deferred(r3, r3)
        self._call_deferred(r1, r1)
        self.assertIs(received[-2], r3)
        self.assertIs(received[-1], r1)
        self.assertEqual(self.slot.free_slots, 2)

        # nothing happens now
        self.clock.advance(5)
        self.assertEqual(len(self.slot.in_progress), 0)
        self.assertEqual(self.slot.free_slots, 2)

    def test_delay(self):
        self.slot.concurrency = 1
        self.slot.delay = 5
        self.slot._clock = self.clock
        self.clock.advance(10)  # so we don't start on time 0

        # enqueue 3 requests
        r1, dfd1 = self._get_request('1')
        self.slot.enqueue(r1, dfd1)
        r2, dfd2 = self._get_request('2')
        self.slot.enqueue(r2, dfd2)
        r3, dfd3 = self._get_request('3')
        self.slot.enqueue(r3, dfd3)
        self.assertEqual(len(self.slot.in_progress), 3)
        self.assertEqual(len(self.slot.transferring), 0)
        self.assertEqual(self.slot.last_download_time, 0)
        self.clock.advance(0)
        self.assertEqual(len(self.slot.transferring), 1)
        self.assertEqual(self.slot.last_download_time, 10)
        self.assertEqual(self.slot.processing.get_time(), 15)

        # download the 1st request
        self._call_deferred(r1, r1)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 0)
        self.assertEqual(self.slot.free_slots, 1)
        # we should still wait
        self.clock.advance(3)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 0)
        self.assertEqual(self.slot.free_slots, 1)
        # make the 2nd request downloading
        self.clock.advance(3)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 1)
        self.assertEqual(self.slot.free_slots, 0)
        self.assertEqual(self.slot.last_download_time, 16)
        self.assertEqual(self.slot.processing.get_time(), 21)
        # wait and nothing happens
        self.clock.advance(10)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 1)
        self.assertFalse(self.slot.processing.is_scheduled())

    def test_fail(self):
        received = []
        def downloaded(result):
            received.append(result)

        # enqueue 3 requests
        r1, dfd1 = self._get_request('1', downloaded)
        self.slot.enqueue(r1, dfd1)
        r2, dfd2 = self._get_request('2', downloaded)
        self.slot.enqueue(r2, dfd2)
        r3, dfd3 = self._get_request('3', downloaded)
        self.slot.enqueue(r3, dfd3)
        self.clock.advance(0)
        # fail the first request
        err = ValueError('my bad')
        self._fail_deferred(r1, err)
        self.assertEqual(received[-1].value, err)
        # other requests should be ok
        self.clock.advance(0)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 2)
        self._call_deferred(r2, r2)
        self.assertEqual(received[-1], r2)
        self._call_deferred(r3, r3)
        self.assertEqual(received[-1], r3)
        self.assertEqual(len(self.slot.in_progress), 0)
        self.assertEqual(len(self.slot.transferring), 0)
