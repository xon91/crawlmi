from twisted.internet.defer import Deferred


def request_deferred(request):
    '''Wrap a request inside a Deferred.

    This returns a Deferred whose first pair of callbacks are the request
    callback and errback.
    '''
    d = Deferred()
    if request.callback:
        d.addCallbacks(request.callback, request.errback)
    request.callback, request.errback = d.callback, d.errback
    return d
