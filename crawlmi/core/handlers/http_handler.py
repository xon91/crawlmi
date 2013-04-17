'''Download handlers for http and https schemes.'''

from twisted.internet import reactor

from crawlmi.compat import optional_features
from crawlmi.exceptions import NotSupported
from crawlmi.core.webclient import (CrawlmiHTPPClientFactory,
        CrawlmiClientContextFactory)


ssl_supported = 'ssl' in optional_features


class HttpDownloadHandler(object):

    def __init__(self, settings):
        self.download_timeout = settings.get_int('DOWNLOAD_TIMEOUT', 180)
        self.download_size_limit = settings.get_int('DOWNLOAD_SIZE_LIMIT', 0)

    def download_request(self, request):
        '''Return a deferred for the HTTP download.'''
        factory = CrawlmiHTPPClientFactory(request, self.download_timeout,
                                           self.download_size_limit)
        self._connect(factory)
        return factory.deferred

    def _connect(self, factory):
        host, port = factory.host, factory.port
        if factory.scheme == 'https':
            if ssl_supported:
                return reactor.connectSSL(host, port, factory,
                        CrawlmiClientContextFactory())
            raise NotSupported('HTTPS not supported: install pyopenssl')
        else:
            return reactor.connectTCP(host, port, factory)
