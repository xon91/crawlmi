'''Download handler for https scheme.'''

from twisted.internet import reactor

from crawlmi.compat import optional_features
from crawlmi.exceptions import NotConfigured
from crawlmi.core.webclient import (CrawlmiHTPPClientFactory,
        CrawlmiClientContextFactory)

ssl_supported = 'ssl' in optional_features
if ssl_supported:
    from OpenSSL import SSL


class HttpsDownloadHandler(object):

    def __init__(self, settings):
        if not ssl_supported:
            raise NotConfigured('HTTPS not supported, install pyopenssl library')
        self.settings = settings
        self.ssl_methods = [SSL.SSLv3_METHOD, SSL.TLSv1_METHOD]

    def download_request(self, request):
        '''Return a deferred for the HTTP download.'''
        dfd = None
        for method in self.ssl_methods:
            if dfd is None:
                dfd = self._download(request, method)
            else:
                def _failure(failure):
                    failure.trap(SSL.Error)
                    return self._download(request, method)
                dfd.addErrback(_failure)
        return dfd

    def _download(self, request, method):
        factory = CrawlmiHTPPClientFactory(
            request,
            self.settings.get_int('DOWNLOAD_TIMEOUT', 180, request),
            self.settings.get_int('DOWNLOAD_SIZE_LIMIT', 0, request))
        host, port = factory.host, factory.port
        bind_address = request.meta.get('bind_address')
        reactor.connectSSL(host, port, factory,
                           CrawlmiClientContextFactory(method),
                           bindAddress=bind_address)
        return factory.deferred
