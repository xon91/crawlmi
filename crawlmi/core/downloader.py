from functools import partial
import random

from twisted.internet import reactor, defer

from crawlmi.core.handlers import GeneralHandler
from crawlmi.queue import MemoryQueue
from crawlmi.utils.defer import LoopingCall, ScheduledCall


class Slot(object):
    '''Slot represents a queue of requests for one particular domain.
    It respects both DOWNLOAD_DELAY and CONCURRENT_REQUESTS_PER_DOMAIN.

    Slot never contains more than CONCURRENT_REQUESTS pending requests, so
    it is a very lightweight structure. All the heavy lifting happens in the
    downloader.
    '''

    def __init__(self, download_handler, concurrency, delay, randomize_delay,
                 clock=None):
        self.download_handler = download_handler
        self.concurrency = concurrency
        self.delay = delay
        self.randomize_delay = randomize_delay
        self.in_progress = set()  # request waiting to be downloaded
        self.transferring = set()  # requests being downloaded (subset of `in_progress`)
        self.last_download_time = 0
        self.queue = MemoryQueue()  # queue of (request, deferred)
        # clock is used in unittests
        self.clock = clock or reactor
        self.delayed_processing = ScheduledCall(self._process, clock=self.clock)

    def enqueue(self, request, dfd):
        '''Main entry point.
        Put the new request to the queue and if possible, start downloading it.
        '''
        def remove_in_progress(response):
            self.in_progress.remove(request)
            return response
        self.in_progress.add(request)
        dfd.addBoth(remove_in_progress)
        self.queue.push((request, dfd))
        self._process()

    @property
    def free_slots(self):
        return self.concurrency - len(self.transferring)

    def is_idle(self):
        return len(self.in_progress) == 0

    def _process(self):
        '''Process the requests in the queue, while respecting the delay and
        concurrency.
        '''
        if self.delayed_processing.is_scheduled() or self._schedule_delay():
            return

        while self.queue and self.free_slots > 0:
            self.last_download_time = self.clock.seconds()
            request, downloaded_dfd = self.queue.pop()
            dfd = self._download(request)
            dfd.chainDeferred(downloaded_dfd)
            if self._schedule_delay():
                return

    def _schedule_delay(self):
        if self.delay:
            penalty = (self.last_download_time + self.get_download_delay() -
                       self.clock.seconds())
            if penalty > 0:
                # following schedule should always be successfull, because
                # `_schedule_delay()` is only called from within `_process()`
                self.delayed_processing.schedule(penalty)
                return True
        return False

    def _download(self, request):
        # download the response
        dfd = self.download_handler.download_request(request)

        # put the request into the set of `transferring` to block other requests
        # after the response is downloaded, remove it from `transferring`
        def remove_transferring(response):
            self.transferring.remove(request)
            self._process()  # process unblocked requests
            return response
        self.transferring.add(request)
        dfd.addBoth(remove_transferring)
        return dfd

    def get_download_delay(self):
        if self.randomize_delay:
            return random.uniform(0.5 * self.delay, 1.5 * self.delay)
        return self.delay


class Downloader(object):
    '''Fetch requests from `inq` queue. When downloaded, put the results into
    `outq` queue. Respect CONCURRENT_REQUESTS setting.
    Requests are further divided into specific slots, based on their domains.

    `inq` can possibly be very big, keep that in mind.

    IMPORTANT - always keep in mind, that if crawlmi is killed unexpectably,
    and `inq` and `outq` are persistent queues, no requests should be lost.
    '''

    def __init__(self, settings, inq, outq, download_handler=None, clock=None):
        self.inq = inq  # queue of requests
        self.outq = outq  # queue of responses
        self.download_handler = download_handler or GeneralHandler(settings)
        self.slots = {}
        self.num_in_progress = 0
        self.clock = clock or reactor
        self.processing = LoopingCall(self.process, clock=self.clock)
        self.processing.schedule()

        self.download_delay = settings.get_int('DOWNLOAD_DELAY')
        self.randomize_delay = settings.get_int(
            'RANDOMIZE_DOWNLOAD_DELAY')
        if self.download_delay:
            self.total_concurrency = self.domain_concurrency = 1
            self.use_domain_specific = False
        else:
            self.total_concurrency = settings.get_int(
                'CONCURRENT_REQUESTS')
            self.domain_concurrency = settings.get_int(
                'CONCURRENT_REQUESTS_PER_DOMAIN')
            if (not self.domain_concurrency or
                    self.domain_concurrency >= self.total_concurrency):
                self.use_domain_specific = False
                self.domain_concurrency = self.total_concurrency
            else:
                self.use_domain_specific = True

    @property
    def free_slots(self):
        return self.total_concurrency - self.num_in_progress

    def is_idle(self):
        return self.num_in_progress == 0

    def process(self):
        while self.inq and self.free_slots > 0:
            request = self.inq.pop()
            key, slot = self._get_slot(request)

            def remove_in_progress(response):
                self.num_in_progress -= 1
                self._clear_slots()  # clear empty slots
                return response

            def enqueue_result(request, response):
                self.outq.push((request, response))
                # don't return anything from here, in a case an error occured

            self.num_in_progress += 1
            dfd = defer.Deferred().addBoth(remove_in_progress)
            dfd.addBoth(partial(enqueue_result, request))
            slot.enqueue(request, dfd)

    def _get_slot(self, request):
        key = request.parsed_url.hostname if self.use_domain_specific else ''
        if key not in self.slots:
            self.slots[key] = Slot(
                self.download_handler,
                self.domain_concurrency,
                self.download_delay,
                self.randomize_delay,
                clock=self.clock)
        return key, self.slots[key]

    def _clear_slots(self):
        '''Clear unused slots and avoid memory leaking.'''
        if len(self.slots) >= 2 * self.total_concurrency:
            to_delete = [k for (k, v) in self.slots.iteritems() if v.is_idle()]
            for key in to_delete:
                del self.slots[key]
