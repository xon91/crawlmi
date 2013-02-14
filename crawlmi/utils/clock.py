from twisted.internet import base
from twisted.internet.interfaces import IReactorTime
from zope.interface import implements


class Clock:
    """
    Provide a deterministic, easily-controlled implementation of
    L{IReactorTime.callLater}.  This is commonly useful for writing
    deterministic unit tests for code which schedules events using this API.

    Crawlmi: Fixes bug when callLater is scheduled from within the delayed call
    with 0 delay. In twisted this causes an infinite loop. But in reactor, it
    works fine.
    """
    implements(IReactorTime)

    rightNow = 0.0

    def __init__(self):
        self._new_calls = []
        self._pending_calls = []


    def seconds(self):
        """
        Pretend to be time.time().  This is used internally when an operation
        such as L{IDelayedCall.reset} needs to determine a a time value
        relative to the current time.

        @rtype: C{float}
        @return: The time which should be considered the current time.
        """
        return self.rightNow


    def _sortCalls(self):
        """
        Sort the pending calls according to the time they are scheduled.
        """
        self._pending_calls.sort(lambda a, b: cmp(a.getTime(), b.getTime()))


    def callLater(self, when, what, *a, **kw):
        """
        See L{twisted.internet.interfaces.IReactorTime.callLater}.
        """
        dc = base.DelayedCall(self.seconds() + when,
                               what, a, kw,
                               self._cancelCallLater,
                               lambda c: None,
                               self.seconds)
        self._new_calls.append(dc)
        return dc

    def _cancelCallLater(self, call):
        if call in self._pending_calls:
            self._pending_calls.remove(call)
        if call in self._new_calls:
            self._new_calls.remove(call)


    def getDelayedCalls(self):
        """
        See L{twisted.internet.interfaces.IReactorTime.getDelayedCalls}
        """
        return self._pending_calls + self._new_calls


    def advance(self, amount):
        """
        Move time on this clock forward by the given amount and run whatever
        pending calls should be run.

        @type amount: C{float}
        @param amount: The number of seconds which to advance this clock's
        time.
        """
        self.rightNow += amount
        self._pending_calls.extend(self._new_calls)
        self._new_calls = []
        self._sortCalls()
        while self._pending_calls and self._pending_calls[0].getTime() <= self.seconds():
            call = self._pending_calls.pop(0)
            call.called = 1
            call.func(*call.args, **call.kw)
            self._sortCalls()


    def pump(self, timings):
        """
        Advance incrementally by the given set of times.

        @type timings: iterable of C{float}
        """
        for amount in timings:
            self.advance(amount)
