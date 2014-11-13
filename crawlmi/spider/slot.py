from functools import partial

from crawlmi.utils.misc import arg_to_iter
from twisted.internet import defer


class Slot(object):
    def __init__(self):
        self.on_start = defer.Deferred()
        self.on_finish = defer.Deferred()

    def start(self):
        self.on_start.callback(self)

    def finish(self):
        self.on_finish.callback(self)


class DownloadSlot(Slot):
    def __init__(self, engine, max_parallel=0):
        super(DownloadSlot, self).__init__()
        self.engine = engine
        self._num_requests_pending = 0
        self.max_parallel = max_parallel
        self._to_schedule = []

    def start(self):
        super(DownloadSlot, self).start()
        requests = self.start_requests()
        self._to_schedule.append(iter(arg_to_iter(requests)))
        self._schedule_requests()

    def _schedule_requests(self):
        while (self._to_schedule and
                (not self.max_parallel or
                 self._num_requests_pending < self.max_parallel)):
            requests = self._to_schedule[-1]
            while (not self.max_parallel or
                    self._num_requests_pending < self.max_parallel):
                try:
                    req = requests.next()
                except StopIteration:
                    self._to_schedule.pop()
                    break
                else:
                    self.engine.download(self._process_request(req))
        if self._num_requests_pending == 0:
            self.finish()

    def _process_request(self, request):
        # ignore requests with no callback specified
        if not request.callback:
            return request
        self._num_requests_pending += 1
        request.callback = partial(self._callback, request.callback)
        request.errback = partial(self._errback, request.errback)
        return request

    def _callback(self, original_callback, response):
        dfd = defer.succeed(response)
        dfd.addCallback(original_callback)
        dfd.addCallback(self._handle_slot_output)
        dfd.addBoth(self._finalize_download)
        return dfd

    def _errback(self, original_errback, failure):
        dfd = defer.fail(failure)
        if original_errback:
            dfd.addErrback(original_errback)
        dfd.addCallback(self._handle_slot_output)
        dfd.addBoth(self._finalize_download)
        return dfd

    def _handle_slot_output(self, result):
        self._to_schedule.append(iter(arg_to_iter(result)))
        # don't return anything, because we schedule the requests by ourselves

    def _finalize_download(self, _value):
        self._num_requests_pending -= 1
        self._schedule_requests()
        return _value

    def start_requests(self):
        pass


class SlotManager(Slot):
    def __init__(self, slot_generator, max_parallel=0):
        super(SlotManager, self).__init__()
        self.slot_generator = iter(slot_generator)
        self.max_parallel = max_parallel
        self.active_slots = set()
        self.scheduling = False

    def start(self):
        super(SlotManager, self).start()
        self._schedule_slots()

    def _schedule_slots(self):
        # break the recursion: _schedule_slots() -> new_slot.start() -> new_slot.finish() -> _schedule_slots()
        if self.scheduling:
            return

        self.scheduling = True
        while (self.slot_generator and
                (not self.max_parallel or
                 len(self.active_slots) < self.max_parallel)):
            try:
                new_slot = self.slot_generator.next()
            except StopIteration:
                self.slot_generator = None
            else:
                new_slot.on_finish.addCallback(self._slot_finished)
                self.active_slots.add(new_slot)
                new_slot.start()
        self.scheduling = False
        if len(self.active_slots) == 0:
            self.finish()

    def _slot_finished(self, slot):
        self.active_slots.remove(slot)
        self._schedule_slots()
        return slot
