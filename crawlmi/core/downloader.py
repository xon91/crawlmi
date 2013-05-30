from functools import partial
import random

from twisted.internet import reactor, defer
from twisted.python.failure import Failure

from crawlmi.core.handlers import GeneralHandler
from crawlmi.queue import MemoryQueue
from crawlmi.utils.defer import LoopingCall, ScheduledCall


class Slot(object):
    '''Slot represents a queue of requests for one particular domain.
    It respects both DOWNLOAD_DELAY and CONCURRENT_REQUESTS_PER_DOMAIN.
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
        dfd = defer.succeed(request)
        # download the response
        dfd.addCallback(self.download_handler.download_request)

        # it is VERY important to wrap the failure into a new object!
        # For errors like ConnectionLost, the same Failure object is returned
        # everytime and we cannot use 'failure.request' field.
        def wrap_failure(failure):
            return Failure(failure.value)
        dfd.addErrback(wrap_failure)

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
    '''Fetch requests from `request_queue` queue. When downloaded,
    put the results into `response_queue` queue. Respect CONCURRENT_REQUESTS
    setting.
    Requests are further divided into specific slots, based on their domains.
    '''

    # how many seconds to wait between the checks of request_queue
    QUEUE_CHECK_FREQUENCY = 0.1

    def __init__(self, settings, request_queue, response_queue,
                 download_handler=None, clock=None):
        self.request_queue = request_queue
        self.response_queue = response_queue  # queue of responses
        self.download_handler = download_handler or GeneralHandler(settings)
        self.slots = {}
        self.num_in_progress = 0
        self.clock = clock or reactor
        self.processing = LoopingCall(self.process, clock=self.clock)
        self.processing.schedule(self.QUEUE_CHECK_FREQUENCY, now=True)
        self.running = True

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

    def close(self):
        self.processing.cancel()
        self.running = False

    @property
    def free_slots(self):
        return self.total_concurrency - self.num_in_progress

    def is_idle(self):
        return self.num_in_progress == 0

    def process(self):
        while (self.running and not self.response_queue.needs_backout() and
                self.request_queue and self.free_slots > 0):
            request = self.request_queue.pop()
            key, slot = self._get_slot(request)

            def remove_in_progress(response):
                self.num_in_progress -= 1
                self._clear_slots()  # clear empty slots
                return response

            def enqueue_result(request, result):
                # in a case, result is actually a Failure
                result.request = request
                # make sure not to modify response_queue, after stopping the downloader
                if self.running:
                    self.response_queue.push(result)
                # don't return anything from here, in a case an error occured -
                # we don't want it to be logged

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
