import re
from cStringIO import StringIO
from time import time
from urlparse import urldefrag

from OpenSSL import SSL
from twisted.internet import defer, reactor, protocol
from twisted.web.http_headers import Headers as TxHeaders
from twisted.web.iweb import IBodyProducer
from twisted.internet.error import TimeoutError
from twisted.web.http import PotentialDataLoss
from twisted.web.client import Agent, ProxyAgent, ResponseDone, HTTPConnectionPool
from twisted.internet.endpoints import TCP4ClientEndpoint
from zope.interface import implements

from crawlmi.exceptions import DownloadSizeError
from crawlmi.http import Headers
from crawlmi.http.response import factory as resp_factory
from crawlmi.core.webclient import _parse_url_args
from crawlmi.core.context_factory import CrawlmiClientContextFactory


class HTTP11DownloadHandler(object):
    def __init__(self, settings):
        self.settings = settings
        self.ssl_methods = settings.get('DOWNLOAD_HANDLER_SSL_METHODS')
        self.context_factories = [CrawlmiClientContextFactory(method) for method in self.ssl_methods]
        self.pool = HTTPConnectionPool(reactor, persistent=True)
        self.pool.maxPersistentPerHost = settings.get_int('CONCURRENT_REQUESTS_PER_DOMAIN')
        self.pool._factory.noisy = False

    def download_request(self, request):
        '''Return a deferred for the HTTP download.'''
        dfd = None
        for context_factory in self.context_factories:
            if dfd is None:
                dfd = self._download(request, context_factory)
            else:
                def _failure(failure):
                    failure.trap(SSL.Error)
                    return self._download(request, context_factory)
                dfd.addErrback(_failure)
        return dfd

    def _download(self, request, context_factory):
        agent = CrawlmiAgent(
            context_factory,
            self.settings.get_float('DOWNLOAD_TIMEOUT', 180, request),
            self.settings.get_int('DOWNLOAD_SIZE_LIMIT', 0, request),
            request.meta.get('bind_address'),
            self.pool)
        return agent.download_request(request)

    def close(self):
        return self.pool.closeCachedConnections()


class TunnelError(Exception):
    '''An HTTP CONNECT tunnel could not be established by the proxy.'''


class TunnelingTCP4ClientEndpoint(TCP4ClientEndpoint):
    '''An endpoint that tunnels through proxies to allow HTTPS downloads. To
    accomplish that, this endpoint sends an HTTP CONNECT to the proxy.
    The HTTP CONNECT is always sent when using this endpoint, I think this could
    be improved as the CONNECT will be redundant if the connection associated
    with this endpoint comes from the pool and a CONNECT has already been issued
    for it.
    '''

    _response_matcher_re = re.compile('HTTP/1\.. 200')

    def __init__(self, reactor, host, port, proxy_conf, context_factory,
                 timeout=180, bind_address=None):
        proxy_host, proxy_port, self._proxy_auth_header = proxy_conf
        super(TunnelingTCP4ClientEndpoint, self).__init__(reactor, proxy_host,
            proxy_port, timeout, bind_address)
        self.tunnel_ready_dfd = defer.Deferred()
        self.tunneled_host = host
        self.tunneled_port = port
        self.context_factory = context_factory

    def request_tunnel(self, protocol):
        '''Asks the proxy to open a tunnel.'''
        tunnel_request = 'CONNECT %s:%s HTTP/1.1\r\n' % (self.tunneled_host,
                                                         self.tunneled_port)
        if self._proxy_auth_header:
            tunnel_request += 'Proxy-Authorization: %s\r\n' % self._proxy_auth_header
        tunnel_request += '\r\n'
        protocol.transport.write(tunnel_request)
        self._protocol_data_received = protocol.dataReceived
        protocol.dataReceived = self.process_proxy_response
        self.protocol = protocol
        return protocol

    def process_proxy_response(self, bytes):
        '''Processes the response from the proxy. If the tunnel is successfully
        created, notifies the client that we are ready to send requests. If not
        raises a TunnelError.
        '''
        self.protocol.dataReceived = self._protocol_data_received
        if TunnelingTCP4ClientEndpoint._response_matcher_re.match(bytes):
            self.protocol.transport.startTLS(self.context_factory,
                                             self.protocol_factory)
            self.tunnel_ready_dfd.callback(self.protocol)
        else:
            self.tunnel_ready_dfd.errback(
                TunnelError('Could not open CONNECT tunnel.'))

    def connect_failed(self, reason):
        '''Propagates the errback to the appropriate deferred.'''
        self.tunnel_ready_dfd.errback(reason)

    def connect(self, protocol_factory):
        self.protocol_factory = protocol_factory
        connect_dfd = super(TunnelingTCP4ClientEndpoint, self).connect(protocol_factory)
        connect_dfd.addCallback(self.request_tunnel)
        connect_dfd.addErrback(self.connect_failed)
        return self.tunnel_ready_dfd


class TunnelingAgent(Agent):
    '''An agent that uses a L{TunnelingTCP4ClientEndpoint} to make HTTPS
    downloads. It may look strange that we have chosen to subclass Agent and not
    ProxyAgent but consider that after the tunnel is opened the proxy is
    transparent to the client; thus the agent should behave like there is no
    proxy involved.
    '''

    def __init__(self, reactor, proxy_conf, context_factory=None,
                 timeout=None, bind_address=None, pool=None):
        super(TunnelingAgent, self).__init__(
            reactor, context_factory, timeout, bind_address, pool)
        self.proxy_conf = proxy_conf
        self.context_factory = context_factory
        self.timeout = timeout
        self.bind_address = bind_address

    def _getEndpoint(self, scheme, host, port):
        return TunnelingTCP4ClientEndpoint(self._reactor, host, port,
            self.proxy_conf, self.context_factory, self.timeout,
            self.bind_address)


class CrawlmiAgent(object):
    def __init__(self, context_factory=None, timeout=180, download_size=0,
                 bind_address=None, pool=None):
        self.context_factory = context_factory
        self.timeout = timeout
        self.download_size = download_size
        self.bind_address = bind_address
        self.pool = pool

    def _get_agent(self, request):
        if request.proxy:
            _, _, proxy_host, proxy_port, proxy_params = _parse_url_args(request.proxy)
            scheme = _parse_url_args(request.url)[0]
            omit_connect_tunnel = proxy_params.find('noconnect') >= 0
            if scheme == 'https' and not omit_connect_tunnel:
                proxy_conf = (proxy_host, proxy_port,
                              request.headers.get('Proxy-Authorization', None))
                return TunnelingAgent(reactor, proxy_conf, self.context_factory,
                    self.timeout, self.bind_address, self.pool)
            else:
                endpoint = TCP4ClientEndpoint(reactor, proxy_host, proxy_port,
                    self.timeout, self.bind_address)
                return ProxyAgent(endpoint)
        return Agent(reactor, self.context_factory, self.timeout, self.bind_address, self.pool)

    def download_request(self, request):
        agent = self._get_agent(request)

        # request details
        url = urldefrag(request.url)[0]
        method = request.method
        headers = TxHeaders(request.headers)
        body_producer = _RequestBodyProducer(request.body) if request.body else None

        start_time = time()
        d = agent.request(method, url, headers, body_producer)
        # set download latency
        d.addCallback(self._cb_latency, request, start_time)
        # response body is ready to be consumed
        d.addCallback(self._cb_body_ready)
        d.addCallback(self._cb_body_done, request, url)
        # check download timeout
        self._timeout_cl = reactor.callLater(self.timeout, d.cancel)
        d.addBoth(self._cb_timeout, request, url, self.timeout)
        return d

    def _cb_timeout(self, result, request, url, timeout):
        if self._timeout_cl.active():
            self._timeout_cl.cancel()
            return result
        raise TimeoutError('Getting %s took longer than %s seconds.' % (url, timeout))

    def _cb_latency(self, result, request, start_time):
        request.meta['download_latency'] = time() - start_time
        return result

    def _cb_body_ready(self, txresponse):
        # deliverBody hangs for responses without body
        if txresponse.length == 0:
            return txresponse, '', None

        def _cancel(_):
            txresponse._transport._producer.loseConnection()

        d = defer.Deferred(_cancel)
        txresponse.deliverBody(_ResponseReader(d, txresponse, self.download_size))
        return d

    def _cb_body_done(self, result, request, url):
        txresponse, body, flags = result
        status = int(txresponse.code)
        headers = Headers(txresponse.headers.getAllRawHeaders())
        response_cls = resp_factory.from_args(headers=headers, url=url)
        return response_cls(url=url, status=status, headers=headers, body=body,
            request=request)


class _RequestBodyProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class _ResponseReader(protocol.Protocol):
    def __init__(self, finished, txresponse, download_size):
        self.finished = finished
        self.txresponse = txresponse
        self.body_buff = StringIO()
        self.download_size = download_size
        self.body_size = 0

    def dataReceived(self, data):
        self.body_size += len(data)
        if self.download_size and self.body_size > self.download_size:
            self.transport.loseConnection()
            self.finished.errback(
                DownloadSizeError('Response exceeded %s bytes.' %
                                  self.download_size))
        self.body_buff.write(data)

    def connectionLost(self, reason):
        if self.finished.called:
            return

        body = self.body_buff.getvalue()
        if reason.check(ResponseDone):
            self.finished.callback((self.txresponse, body, None))
        elif reason.check(PotentialDataLoss):
            self.finished.callback((self.txresponse, body, ['partial']))
        else:
            self.finished.errback(reason)
