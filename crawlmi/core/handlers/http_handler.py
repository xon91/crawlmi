'''Download handler for http scheme.'''

from twisted.internet import reactor

from crawlmi.core.webclient import CrawlmiHTPPClientFactory


class HttpDownloadHandler(object):

    def __init__(self, settings):
        self.settings = settings

    def download_request(self, request):
        '''Return a deferred for the HTTP download.'''
        factory = CrawlmiHTPPClientFactory(
            request,
            self.settings.get_int('DOWNLOAD_TIMEOUT', 180, request),
            self.settings.get_int('DOWNLOAD_SIZE_LIMIT', 0, request))
        host, port = factory.host, factory.port
        bind_address = request.meta.get('bind_address')
        reactor.connectTCP(host, port, factory, bindAddress=bind_address)
        return factory.deferred
