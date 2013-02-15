from twisted.internet import defer
from twisted.python.failure import Failure

from crawlmi import log
from crawlmi.xlib.pydispatch import dispatcher
from crawlmi.xlib.pydispatch.dispatcher import (Any, Anonymous, liveReceivers,
    getAllReceivers, disconnect)
from crawlmi.xlib.pydispatch.robustapply import robustApply


class SignalManager(object):
    def __init__(self, sender=Anonymous):
        self.sender = sender

    def connect(self, *args, **kwargs):
        kwargs.setdefault('sender', self.sender)
        return dispatcher.connect(*args, **kwargs)

    def disconnect(self, *args, **kwargs):
        kwargs.setdefault('sender', self.sender)
        return dispatcher.disconnect(*args, **kwargs)

    def send(self, signal=Any, *args, **kwargs):
        sender = kwargs.pop('sender', self.sender)
        dont_log = kwargs.pop('dont_log', None)
        responses = []
        for receiver in liveReceivers(getAllReceivers(sender, signal)):
            try:
                response = robustApply(receiver, signal=signal, sender=sender,
                                       *args, **kwargs)
                if isinstance(response, defer.Deferred):
                    log.msg(format="Cannot return deferreds from signal handler: %(receiver)s",
                            level=log.ERROR, receiver=receiver)
            except dont_log:
                result = Failure()
            except Exception:
                result = Failure()
                log.err(result, "Error caught on signal handler: %s" % receiver)
            else:
                result = response
            responses.append((receiver, result))
        return responses

    def send_deferred(self, signal=Any, *args, **kwargs):
        sender = kwargs.pop('sender', self.sender)
        dont_log = kwargs.pop('dont_log', None)

        def logerror(failure, recv):
            if dont_log is None or not isinstance(failure.value, dont_log):
                log.err(failure, "Error caught on signal handler: %s" % recv)
            return failure

        dfds = []
        for receiver in liveReceivers(getAllReceivers(sender, signal)):
            dfd = defer.maybeDeferred(robustApply, receiver, signal=signal,
                                    sender=sender, *args, **kwargs)
            dfd.addErrback(logerror, receiver)
            dfd.addBoth(lambda result: (receiver, result))
            dfds.append(dfd)
        dfd = defer.DeferredList(dfds)
        dfd.addCallback(lambda out: [x[1] for x in out])
        return dfd

    def disconnect_all(self, signal=Any, sender=None):
        sender = self.sender if sender is None else sender
        for receiver in liveReceivers(getAllReceivers(sender, signal)):
            disconnect(receiver, signal=signal, sender=sender)
