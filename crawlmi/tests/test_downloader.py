from twisted.internet import defer
from twisted.python.failure import Failure
from twisted.trial import unittest

from crawlmi.core.downloader import Slot, Downloader
from crawlmi.http import Request, Response
from crawlmi.queue import MemoryQueue, ResponseQueue
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


class ExceptionDownloaderHandler(object):
    def __init__(self, settings):
        pass

    def download_request(self, request):
        raise Exception()


class FailureDownloaderHandler(object):
    failure = Failure(ValueError())

    def __init__(self, settings):
        pass

    def download_request(self, request):
        return self.failure


def get_request(domain='github', func=None):
    dfd = defer.Deferred()
    if func:
        dfd.addBoth(func)
    return (Request('http://www.%s.com/' % domain), dfd)


class DownloaderSlotTest(unittest.TestCase):
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

    def test_exception(self):
        self.slot.download_handler = ExceptionDownloaderHandler(Settings())
        r1, dfd1 = get_request('1')
        self.slot.enqueue(r1, dfd1)
        return self.assertFailure(dfd1, Exception)

    def test_failure(self):
        self.slot.download_handler = FailureDownloaderHandler(Settings())
        download_values = []
        def downloaded(value):
            download_values.append(value)

        for i in xrange(2):
            r, dfd = get_request(str(i))
            dfd.addBoth(downloaded)
            self.slot.enqueue(r, dfd)

        self.assertEqual(len(download_values), 2)
        self.assertIsInstance(download_values[0], Failure)
        self.assertIsInstance(download_values[1], Failure)
        self.assertIsNot(download_values[0], download_values[1])
        self.assertIsInstance(download_values[0].value, ValueError)

class DownloaderTest(unittest.TestCase):

    default_settings = {
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 0,
        'RANDOMIZE_DOWNLOAD_DELAY': False}

    def setUp(self):
        self.clock = Clock()
        self.request_queue = MemoryQueue()
        self.response_queue = ResponseQueue()
        self.dwn = Downloader(Settings(self.default_settings), self.request_queue,
                              self.response_queue,
                              download_handler=MockDownloaderHandler(Settings()),
                              clock=self.clock)
        self.handler = self.dwn.download_handler

    def _update_dwn(self, **kwargs):
        '''Update downloader with the new settings.
        '''
        new_settings = self.default_settings.copy()
        new_settings.update(**kwargs)
        self.dwn.processing.cancel()
        self.dwn = Downloader(Settings(new_settings), self.request_queue, self.response_queue,
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
                      DOWNLOAD_DELAY=3.14)
        self.assertEqual(self.dwn.download_delay, 3.14)
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
        map(lambda r: self.request_queue.push(r), requests)
        self.assertEqual(self.dwn.free_slots, 2)
        self.assertTrue(self.dwn.is_idle())

        # start downloading first two requests
        self.clock.advance(0)
        self.assertEqual(self.dwn.free_slots, 0)
        self.assertFalse(self.dwn.is_idle())
        # no more requests are scheduled, until download is finished
        self.clock.advance(20)
        self.assertEqual(len(self.request_queue), 3)
        # download the first request
        self.handler.call(requests[0], Response('hello'))
        self.assertEqual(self.dwn.free_slots, 1)  # slot is immediately available
        # result is also available
        result = self.response_queue.peek()
        self.assertIs(result.request, requests[0])
        self.assertEqual(result.url, 'hello')
        # enqueue third request
        self.clock.advance(Downloader.QUEUE_CHECK_FREQUENCY)
        self.assertEqual(self.dwn.free_slots, 0)
        # download second request
        self.handler.call(requests[1], Response(''))
        # enqueue fourth request
        self.clock.advance(Downloader.QUEUE_CHECK_FREQUENCY)
        self.assertEqual(self.dwn.free_slots, 0)
        # fourth request should not begin download, until 3rd request is done
        self.assertRaises(KeyError, self.handler.call, requests[3], Response(''))
        # finish
        self.handler.call(requests[2], Response(''))
        self.handler.call(requests[3], Response(''))
        self.clock.advance(Downloader.QUEUE_CHECK_FREQUENCY)
        self.handler.call(requests[4], Response(''))
        # final checks
        self.clock.pump([1] * 10)
        self.assertEqual(len(self.response_queue), 5)
        self.assertTrue(self.dwn.is_idle())

    def test_close(self):
        req1 = get_request('a')[0]
        req2 = get_request('b')[0]
        self.request_queue.push(req1)
        self.clock.advance(20)
        self.request_queue.push(req2)
        # test basic attributes, before and after closing
        self.assertTrue(self.dwn.running)
        self.assertTrue(self.dwn.processing.is_scheduled())
        self.dwn.close()
        self.assertFalse(self.dwn.running)
        self.assertFalse(self.dwn.processing.is_scheduled())

        self.clock.advance(20)
        self.assertEqual(len(self.request_queue), 1)  # request 2 remains unqueued

        # downloader behavior after closing
        self.assertEqual(len(self.response_queue), 0)
        self.handler.call(req1, Response(''))
        self.assertEqual(len(self.response_queue), 0)

    def test_fail(self):
        self._update_dwn(CONCURRENT_REQUESTS=3, CONCURRENT_REQUESTS_PER_DOMAIN=2)
        requests = [get_request(id)[0] for id in 'aab']
        map(lambda r: self.request_queue.push(r), requests)

        # enqueue requests
        self.clock.advance(0)
        # fail 1st request
        err = ValueError('my bad')
        self.handler.fail(requests[0], err)
        self.assertEqual(self.dwn.free_slots, 1)
        fail = self.response_queue.pop()
        self.assertIs(fail.request, requests[0])
        self.assertIs(fail.value, err)
        # fail 3rd request
        self.handler.fail(requests[2], err)
        fail = self.response_queue.pop()
        self.assertIs(fail.request, requests[2])
        self.assertIs(fail.value, err)
        # succeed 2nd request
        self.handler.call(requests[1], Response('nice!', request=requests[1]))
        resp = self.response_queue.pop()
        self.assertIs(resp.request, requests[1])
        self.assertEqual(resp.url, 'nice!')

    def test_clear_slots(self):
        requests = [get_request(id)[0] for id in xrange(30)]
        for r in requests:
            self.request_queue.push(r)
            self.clock.advance(Downloader.QUEUE_CHECK_FREQUENCY)
            self.handler.call(r, Response(''))
        self.assertLessEqual(len(self.dwn.slots), 2 * self.dwn.total_concurrency)
