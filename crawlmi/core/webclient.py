from time import time
from urlparse import urlparse, urlunparse, urldefrag

from twisted.web.client import HTTPClientFactory
from twisted.web.http import HTTPClient
from twisted.internet import defer

from crawlmi.compat import optional_features
from crawlmi.http.headers import Headers
from crawlmi.http.response import Response


class BadHttpHeaderError(Exception):
    '''Raised when bad http header have beed received.
    '''


class CrawlmiHTTPClient(HTTPClient):

    delimiter = '\n'

    def connectionMade(self):
        self.headers = Headers()

        # method command
        self.sendCommand(self.factory.method, self.factory.path)
        # headers
        for key, values in self.factory.headers.iteritems():
            for value in values:
                self.sendHeader(key, value)
        self.endHeaders()
        # body
        if self.factory.body is not None:
            self.transport.write(self.factory.body)

    def extractHeader(self, header):
        key, val = header.split(':', 1)
        val = val.lstrip()
        self.handleHeader(key, val)
        if key.lower() == 'content-length':
            self.length = int(val)

    def lineReceived(self, line):
        try:
            HTTPClient.lineReceived(self, line.rstrip())
        except:
            self.factory.invalid_headers.append(line)
            if hasattr(self.transport, 'abortConnection'):
                self.transport.abortConnection()
            else:
                self.transport.loseConnection()

    def handleHeader(self, key, value):
        self.headers.appendlist(key, value)

    def handleStatus(self, version, status, message):
        self.factory.gotStatus(version, status, message)

    def handleEndHeaders(self):
        self.factory.gotHeaders(self.headers)

    def connectionLost(self, reason):
        HTTPClient.connectionLost(self, reason)
        self.factory.noPage(reason)

    def handleResponse(self, response):
        if self.factory.method.upper() == 'HEAD':
            self.factory.page('')
        else:
            self.factory.page(response)
        self.transport.loseConnection()

    def timeout(self):
        self.transport.loseConnection()
        self.factory.noPage(
                defer.TimeoutError('Getting %s took longer than %s seconds.' %
                                   (self.factory.url, self.factory.timeout)))


class CrawlmiHTPPClientFactory(HTTPClientFactory):
    protocol = CrawlmiHTTPClient
    waiting = 1
    noisy = False
    followRedirect = False
    afterFoundGet = False

    def __init__(self, request, timeout=180):
        self.url = urldefrag(request.url)[0]
        self.method = request.method
        self.body = request.body or None
        self.headers = Headers(request.headers)
        self.response_headers = None
        self.timeout = timeout
        self.start_time = time()
        self.deferred = defer.Deferred()
        self.deferred.addCallback(self._build_response, request)
        self.invalid_headers = []

        # Fixes Twisted 11.1.0+ support as HTTPClientFactory is expected
        # to have _disconnectedDeferred. See Twisted r32329.
        # As Scrapy implements it's own logic to handle redirects is not
        # needed to add the callback _waitForDisconnect.
        # Specifically this avoids the AttributeError exception when
        # clientConnectionFailed method is called.
        self._disconnectedDeferred = defer.Deferred()

        self._set_connection_attributes(request)

        # set Host header based on url
        self.headers.setdefault('Host', self.netloc)

        # set Content-Length based len of body
        if self.body is not None:
            self.headers['Content-Length'] = len(self.body)
        # just in case a broken http/1.1 decides to keep connection alive
        self.headers.setdefault('Connection', 'close')

    def _build_response(self, body, request):
        if self.invalid_headers:
            raise BadHttpHeaderError('Invalid headers received: %s' %
                                     self.invalid_headers)

        response = Response(url=self.url, status=self.status,
            headers=self.response_headers, body=body, request=request)
        response.download_latency = self.headers_time - self.start_time
        return response

    def _set_connection_attributes(self, request):
        self.scheme, self.netloc, self.host, self.port, self.path = \
            self._parse_url_args(request.url)
        if request.proxy:
            self.scheme, _, self.host, self.port, _ = \
                self._parse_url_args(request.proxy)
            self.path = self.url

    def _parse_url_args(self, url):
        parsed = urlparse(url.strip())
        path = urlunparse(('', '', parsed.path or '/', parsed.params,
                           parsed.query, ''))
        host = parsed.hostname
        port = parsed.port
        scheme = parsed.scheme
        netloc = parsed.netloc
        if port is None:
            port = 443 if scheme == 'https' else 80
        return scheme, netloc, host, port, path

    def gotStatus(self, version, status, message):
        self.version, self.status, self.message = version, int(status), message

    def gotHeaders(self, headers):
        self.headers_time = time()
        self.response_headers = headers


if 'ssl' in optional_features:
    from twisted.internet.ssl import ClientContextFactory
    from OpenSSL import SSL
else:
    ClientContextFactory = object


class CrawlmiClientContextFactory(ClientContextFactory):
    'A SSL context factory which is more permissive against SSL bugs.'
    # see https://github.com/scrapy/scrapy/issues/82
    # and https://github.com/scrapy/scrapy/issues/26

    def __init__(self):
        # see this issue on why we use TLSv1_METHOD by default
        # https://github.com/scrapy/scrapy/issues/194
        self.method = SSL.TLSv1_METHOD

    def getContext(self):
        ctx = ClientContextFactory.getContext(self)
        # Enable all workarounds to SSL bugs as documented by
        # http://www.openssl.org/docs/ssl/SSL_CTX_set_options.html
        ctx.set_options(SSL.OP_ALL)
        return ctx
