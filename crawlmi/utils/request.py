from urlparse import urlunparse

from twisted.internet.defer import Deferred


def request_http_repr(request):
    '''Return the raw HTTP representation (as string) of the given request.
    This is provided only for reference since it's not the actual stream of
    bytes that will be send when performing the request (that's controlled
    by Twisted).
    '''
    parsed = request.parsed_url
    path = urlunparse(('', '', parsed.path or '/', parsed.params, parsed.query, ''))
    s = '%s %s HTTP/1.1\r\n' % (request.method, path)
    s += 'Host: %s\r\n' % parsed.hostname
    if request.headers:
        s += request.headers.to_string() + '\r\n'
    s += '\r\n'
    s += request.body
    return s


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
