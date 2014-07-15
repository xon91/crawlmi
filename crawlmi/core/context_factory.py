from twisted.internet.ssl import ClientContextFactory
from OpenSSL import SSL


class CrawlmiClientContextFactory(ClientContextFactory):
    'A SSL context factory which is more permissive against SSL bugs.'
    # see https://github.com/scrapy/scrapy/issues/82
    # and https://github.com/scrapy/scrapy/issues/26

    def __init__(self, method):
        # see this issue on why we use TLSv1_METHOD by default
        # https://github.com/scrapy/scrapy/issues/194
        # self.method = SSL.TLSv1_METHOD
        # try following method if TLSv1_METHOD fails
        # self.method = SSL.SSLv3_METHOD
        self.method = method

    def getContext(self, hostname=None, port=None):
        ctx = ClientContextFactory.getContext(self)
        # Enable all workarounds to SSL bugs as documented by
        # http://www.openssl.org/docs/ssl/SSL_CTX_set_options.html
        ctx.set_options(SSL.OP_ALL)
        return ctx
