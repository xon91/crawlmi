from time import time
from urlparse import urlparse, urlunparse, urldefrag

from twisted.web.client import HTTPClientFactory
from twisted.web.http import HTTPClient
from twisted.internet import defer

from crawlmi.exceptions import DownloadSizeError
from crawlmi.http import Headers
from crawlmi.http.response import factory as resp_factory


def _parse_url_args(url):
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


class BadHttpHeaderError(Exception):
    '''Raised when bad http header have beed received.
    '''


class CrawlmiHTTPClient(HTTPClient):

    delimiter = '\n'

    def __init__(self):
        self.body_size = 0

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
        self.headers.add(key, value)

    def handleStatus(self, version, status, message):
        self.factory.gotStatus(version, status, message)

    def handleEndHeaders(self):
        self.factory.gotHeaders(self.headers)

    def connectionLost(self, reason):
        self._connection_lost_reason = reason
        HTTPClient.connectionLost(self, reason)
        self.factory.noPage(reason)

    def handleResponse(self, response):
        if self.factory.method.upper() == 'HEAD':
            self.factory.page('')
        elif self.length is not None and self.length > 0:
            self.factory.noPage(self._connection_lost_reason)
        else:
            self.factory.page(response)
        self.transport.loseConnection()

    def timeout(self):
        self.transport.loseConnection()
        self.factory.noPage(
            defer.TimeoutError('Getting %s took longer than %s seconds.' %
                               (self.factory.url, self.factory.timeout)))

    def handleResponsePart(self, data):
        HTTPClient.handleResponsePart(self, data)
        self.body_size += len(data)
        if (self.factory.download_size and
                self.body_size > self.factory.download_size):
            self.transport.loseConnection()
            self.factory.noPage(
                DownloadSizeError('Response exceeded %s bytes.' %
                                  self.factory.download_size))


class CrawlmiHTPPClientFactory(HTTPClientFactory):
    protocol = CrawlmiHTTPClient
    waiting = 1
    noisy = False
    followRedirect = False
    afterFoundGet = False

    def __init__(self, request, timeout=180, download_size=0):
        self.url = urldefrag(request.url)[0]
        self.method = request.method
        self.body = request.body or None
        self.headers = Headers(request.headers)
        self.response_headers = None
        self.start_time = time()
        self.deferred = defer.Deferred()
        self.deferred.addCallback(self._build_response, request)
        self.invalid_headers = []
        self.timeout = timeout
        self.download_size = download_size

        # Fixes Twisted 11.1.0+ support as HTTPClientFactory is expected
        # to have _disconnectedDeferred. See Twisted r32329.
        # As Crawlmi implements it's own logic to handle redirects is not
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

        response_cls = resp_factory.from_args(headers=self.response_headers,
                                              url=self.url)
        response = response_cls(
            url=self.url, status=self.status, headers=self.response_headers,
            body=body, request=request)
        response.download_latency = self.headers_time - self.start_time
        return response

    def _set_connection_attributes(self, request):
        self.scheme, self.netloc, self.host, self.port, self.path = \
            _parse_url_args(request.url)
        if request.proxy:
            self.scheme, _, self.host, self.port, _ = \
                _parse_url_args(request.proxy)
            self.path = self.url

    def gotStatus(self, version, status, message):
        self.version, self.status, self.message = version, int(status), message

    def gotHeaders(self, headers):
        self.headers_time = time()
        self.response_headers = headers
