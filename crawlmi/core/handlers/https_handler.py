'''Download handler for https scheme.'''

from OpenSSL import SSL
from twisted.internet import reactor

from crawlmi.core.webclient import CrawlmiHTPPClientFactory
from crawlmi.core.context_factory import  CrawlmiClientContextFactory


class HttpsDownloadHandler(object):

    def __init__(self, settings):
        self.settings = settings
        self.ssl_methods = settings.get('DOWNLOAD_HANDLER_SSL_METHODS')

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
            self.settings.get_float('DOWNLOAD_TIMEOUT', 180, request),
            self.settings.get_int('DOWNLOAD_SIZE_LIMIT', 0, request))
        host, port = factory.host, factory.port
        bind_address = request.meta.get('bind_address')
        reactor.connectSSL(host, port, factory,
                           CrawlmiClientContextFactory(method, host, port),
                           bindAddress=bind_address)
        return factory.deferred
