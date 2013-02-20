import unittest2

from twisted.internet import defer
from twisted.python.failure import Failure

from crawlmi.core.downloader import Slot, Downloader
from crawlmi.http.request import Request
from crawlmi.http.response import Response
from crawlmi.queue import MemoryQueue
from crawlmi.settings import Settings
from crawlmi.utils.clock import Clock


class MockDownloaderHandler(object):
    def __init__(self, settings):
        self.dfds = {}

    def download_request(self, request):
        dfd = defer.Deferred()
        self.dfds[request] = dfd
        return dfd

    def call(self, request, response):
        response.request = request
        self.dfds[request].callback(response)

    def fail(self, request, error):
        self.dfds[request].errback(Failure(error))


def get_request(domain='github', func=None):
    dfd = defer.Deferred()
    if func:
        dfd.addBoth(func)
    return (Request('http://www.%s.com/' % domain), dfd)


class DownloaderSlotTest(unittest2.TestCase):
    default_concurrency = 2
    default_delay = 0
    default_randomize_delay = False

    def setUp(self):
        self.handler = MockDownloaderHandler(Settings())
        self.clock = Clock()
        self.slot = Slot(self.handler, self.default_concurrency,
                         self.default_delay, self.default_randomize_delay,
                         clock=self.clock)

    def test_basic(self):
        received = []
        def downloaded(result):
            received.append(result)

        # enqueue 3 requests
        r1, dfd1 = get_request('1', func=downloaded)
        self.slot.enqueue(r1, dfd1)
        self.assertEqual(len(self.slot.in_progress), 1)
        self.assertEqual(len(self.slot.transferring), 1)
        r2, dfd2 = get_request('2', func=downloaded)
        r3, dfd3 = get_request('3', func=downloaded)
        self.slot.enqueue(r2, dfd2)
        self.slot.enqueue(r3, dfd3)
        self.assertEqual(len(self.slot.in_progress), 3)
        self.assertEqual(len(self.slot.transferring), 2)
        self.assertEqual(self.slot.free_slots, 0)

        # download r2
        self.handler.call(r2, Response(''))
        self.assertIs(received[-1].request, r2)
        self.assertEqual(len(self.slot.transferring), 2)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(self.slot.free_slots, 0)

        # download r1 and r3
        self.handler.call(r3, Response(''))
        self.handler.call(r1, Response(''))
        self.assertIs(received[-2].request, r3)
        self.assertIs(received[-1].request, r1)
        self.assertEqual(self.slot.free_slots, 2)

        # nothing happens now
        self.clock.advance(5)
        self.assertEqual(len(self.slot.in_progress), 0)
        self.assertEqual(self.slot.free_slots, 2)

    def test_delay(self):
        self.slot.concurrency = 1
        self.slot.delay = 5
        self.clock.advance(10)  # so we don't start on time 0

        # enqueue 3 requests
        r1, dfd1 = get_request('1')
        self.slot.enqueue(r1, dfd1)
        r2, dfd2 = get_request('2')
        self.slot.enqueue(r2, dfd2)
        r3, dfd3 = get_request('3')
        self.slot.enqueue(r3, dfd3)
        self.assertEqual(len(self.slot.in_progress), 3)
        self.assertEqual(len(self.slot.transferring), 1)
        self.assertEqual(self.slot.last_download_time, 10)
        self.assertEqual(self.slot.delayed_processing.get_time(), 15)

        # download the 1st request
        self.handler.call(r1, Response(''))
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
        self.assertEqual(self.slot.delayed_processing.get_time(), 21)
        # wait and nothing happens
        self.clock.advance(10)
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 1)
        self.assertFalse(self.slot.delayed_processing.is_scheduled())

    def test_random_delay(self):
        self.slot.delay = 5
        self.slot.randomize_delay = False
        delays = [self.slot.get_download_delay() for x in xrange(10)]
        self.assertTrue(all(x == 5 for x in delays))

        self.slot.randomize_delay = True
        lower = 0.5 * 5
        upper = 1.5 * 5
        delays = [self.slot.get_download_delay() for x in xrange(100)]
        self.assertTrue(all(lower <= x <= upper for x in delays))

        third1 = (2 * lower + upper) / 3
        third2 = (lower + 2 * upper) / 3
        self.assertTrue(any(x <= third1 for x in delays))
        self.assertTrue(any(third1 <= x <= third2 for x in delays))
        self.assertTrue(any(third2 <= x for x in delays))

    def test_fail(self):
        received = []
        def downloaded(result):
            received.append(result)

        # enqueue 3 requests
        r1, dfd1 = get_request('1', func=downloaded)
        self.slot.enqueue(r1, dfd1)
        r2, dfd2 = get_request('2', func=downloaded)
        self.slot.enqueue(r2, dfd2)
        r3, dfd3 = get_request('3', func=downloaded)
        self.slot.enqueue(r3, dfd3)
        # fail the first request
        err = ValueError('my bad')
        self.handler.fail(r1, err)
        self.assertEqual(received[-1].value, err)
        # other requests should be ok
        self.assertEqual(len(self.slot.in_progress), 2)
        self.assertEqual(len(self.slot.transferring), 2)
        self.handler.call(r2, Response(''))
        self.assertEqual(received[-1].request, r2)
        self.handler.call(r3, Response(''))
        self.assertEqual(received[-1].request, r3)
        self.assertEqual(len(self.slot.in_progress), 0)
        self.assertEqual(len(self.slot.transferring), 0)


class DownloaderTest(unittest2.TestCase):

    default_settings = Settings({
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 0,
        'RANDOMIZE_DOWNLOAD_DELAY': False
    })

    def setUp(self):
        self.clock = Clock()
        self.inq = MemoryQueue()
        self.outq = MemoryQueue()
        self.dwn = Downloader(self.default_settings, self.inq,
                              self.outq,
                              download_handler=MockDownloaderHandler(Settings()),
                              clock=self.clock)
        self.handler = self.dwn.download_handler

    def _update_dwn(self, **kwargs):
        '''Update downloader with the new settings.
        '''
        settings = self.default_settings.copy()
        settings.update(**kwargs)
        self.dwn.processing.cancel()
        self.dwn = Downloader(settings, self.inq, self.outq,
                              download_handler=MockDownloaderHandler(Settings()),
                              clock=self.clock)
        self.handler = self.dwn.download_handler

    def test_concurrency(self):
        # standard situation
        self._update_dwn()
        self.assertEqual(self.dwn.total_concurrency, 2)
        self.assertEqual(self.dwn.domain_concurrency, 1)
        self.assertTrue(self.dwn.use_domain_specific)
        # delay set
        self._update_dwn(CONCURRENT_REQUESTS=10, CONCURRENT_REQUESTS_PER_DOMAIN=5,
                      DOWNLOAD_DELAY=5)
        self.assertEqual(self.dwn.total_concurrency, 1)
        self.assertEqual(self.dwn.domain_concurrency, 1)
        self.assertFalse(self.dwn.use_domain_specific)
        # domain concurrency is 0
        self._update_dwn(CONCURRENT_REQUESTS=10, CONCURRENT_REQUESTS_PER_DOMAIN=0)
        self.assertEqual(self.dwn.total_concurrency, 10)
        self.assertEqual(self.dwn.domain_concurrency, 10)
        self.assertFalse(self.dwn.use_domain_specific)
        # domain concurrency is too big
        self._update_dwn(CONCURRENT_REQUESTS=5, CONCURRENT_REQUESTS_PER_DOMAIN=10)
        self.assertEqual(self.dwn.total_concurrency, 5)
        self.assertEqual(self.dwn.domain_concurrency, 5)
        self.assertFalse(self.dwn.use_domain_specific)
        self._update_dwn(CONCURRENT_REQUESTS=5, CONCURRENT_REQUESTS_PER_DOMAIN=5)
        self.assertFalse(self.dwn.use_domain_specific)

    def test_get_slot(self):
        key, slot = self.dwn._get_slot(Request('http://www.github.com/'))
        self.assertEqual(key, 'www.github.com')
        key2, slot2 = self.dwn._get_slot(Request('http://www.github.com/hello/world#bla'))
        self.assertEqual(key2, 'www.github.com')
        self.assertIs(slot2, slot)
        key3, slot3 = self.dwn._get_slot(Request('http://sites.github.com/'))
        self.assertEqual(key3, 'sites.github.com')
        self.assertIsNot(slot3, slot)
        self.assertEqual(len(self.dwn.slots), 2)

        # don't use domain specific slots
        self.dwn.use_domain_specific = False
        key, slot = self.dwn._get_slot(Request('http://www.github.com/'))
        self.assertEqual(key, '')
        key2, slot2 = self.dwn._get_slot(Request('http://sites.github.com/'))
        self.assertIs(slot2, slot)

    def test_basic(self):
        # create 5 requests with slot ids: a, b, a, a, c
        requests = [get_request(id)[0] for id in 'abaac']
        map(lambda r: self.inq.push(r), requests)
        self.assertEqual(self.dwn.free_slots, 2)
        self.assertTrue(self.dwn.is_idle())

        # start downloading first two requests
        self.clock.advance(0)
        self.assertEqual(self.dwn.free_slots, 0)
        self.assertFalse(self.dwn.is_idle())
        # no more requests are scheduled, until download is finished
        self.clock.advance(20)
        self.assertEqual(len(self.inq), 3)
        # download the first request
        self.handler.call(requests[0], Response('hello'))
        self.assertEqual(self.dwn.free_slots, 1)  # slot is immediately available
        # result is also available
        result = self.outq.peek()
        self.assertIs(result.request, requests[0])
        self.assertEqual(result.url, 'hello')
        # enqueue third request
        self.clock.advance(0)
        self.assertEqual(self.dwn.free_slots, 0)
        # download second request
        self.handler.call(requests[1], Response(''))
        # enqueue fourth request
        self.clock.advance(0)
        self.assertEqual(self.dwn.free_slots, 0)
        # fourth request should not begin download, until 3rd request is done
        self.assertRaises(KeyError, self.handler.call, requests[3], Response(''))
        # finish
        self.handler.call(requests[2], Response(''))
        self.handler.call(requests[3], Response(''))
        self.clock.advance(0)
        self.handler.call(requests[4], Response(''))
        # final checks
        self.clock.pump([1] * 10)
        self.assertEqual(len(self.outq), 5)
        self.assertTrue(self.dwn.is_idle())

    def test_fail(self):
        self._update_dwn(CONCURRENT_REQUESTS=3, CONCURRENT_REQUESTS_PER_DOMAIN=2)
        requests = [get_request(id)[0] for id in 'aab']
        map(lambda r: self.inq.push(r), requests)

        # enqueue requests
        self.clock.advance(0)
        # fail 1st request
        err = ValueError('my bad')
        self.handler.fail(requests[0], err)
        self.assertEqual(self.dwn.free_slots, 1)
        fail = self.outq.pop()
        self.assertIs(fail.request, requests[0])
        self.assertIs(fail.value, err)
        # fail 3rd request
        self.handler.fail(requests[2], err)
        fail = self.outq.pop()
        self.assertIs(fail.request, requests[2])
        self.assertIs(fail.value, err)
        # succeed 2nd request
        self.handler.call(requests[1], Response('nice!', request=requests[1]))
        resp = self.outq.pop()
        self.assertIs(resp.request, requests[1])
        self.assertEqual(resp.url, 'nice!')

    def test_clear_slots(self):
        requests = [get_request(id)[0] for id in xrange(30)]
        for r in requests:
            self.inq.push(r)
            self.clock.advance(0)
            self.handler.call(r, Response(''))
        self.assertLessEqual(len(self.dwn.slots), 2 * self.dwn.total_concurrency)
