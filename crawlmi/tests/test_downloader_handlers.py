import os

from twisted.internet import reactor
from twisted.protocols.policies import WrappingFactory
from twisted.python.filepath import FilePath
from twisted.trial import unittest
from twisted.web import server, static, util, resource
from twisted.web.test.test_webclient import (ForeverTakingResource,
        NoLengthResource, HostHeaderResource,
        PayloadResource, BrokenDownloadResource)

from crawlmi.core.handlers import (FileDownloadHandler, HttpDownloadHandler,
        GeneralHandler)
from crawlmi.exceptions import NotConfigured, NotSupported
from crawlmi.http import Request
from crawlmi.settings import Settings
from crawlmi.utils.url import path_to_file_uri


class FileTest(unittest.TestCase):

    def setUp(self):
        self.tmpname = self.mktemp()
        fd = open(self.tmpname + '^', 'w')
        fd.write('0123456789')
        fd.close()
        self.download_request = FileDownloadHandler(Settings()).download_request

    def test_download(self):
        def _test(response):
            self.assertEquals(response.url, request.url)
            self.assertEquals(response.status, 200)
            self.assertEquals(response.body, '0123456789')

        request = Request(path_to_file_uri(self.tmpname + '^'))
        self.assertTrue(request.url.upper().endswith('%5E'))
        return self.download_request(request).addCallback(_test)

    def test_non_existent(self):
        request = Request('file://%s' % self.mktemp())
        d = self.download_request(request)
        return self.assertFailure(d, IOError)


class HttpTest(unittest.TestCase):

    def setUp(self):
        name = self.mktemp()
        os.mkdir(name)
        FilePath(name).child('file').setContent('0123456789')
        r = static.File(name)
        r.putChild('redirect', util.Redirect('/file'))
        r.putChild('wait', ForeverTakingResource())
        r.putChild('nolength', NoLengthResource())
        r.putChild('host', HostHeaderResource())
        r.putChild('payload', PayloadResource())
        r.putChild('broken', BrokenDownloadResource())
        self.site = server.Site(r, timeout=None)
        self.wrapper = WrappingFactory(self.site)
        self.port = reactor.listenTCP(0, self.wrapper, interface='127.0.0.1')
        self.portno = self.port.getHost().port
        self.download_request = HttpDownloadHandler(Settings()).download_request

    def tearDown(self):
        return self.port.stopListening()

    def getURL(self, path):
        return 'http://127.0.0.1:%d/%s' % (self.portno, path)

    def test_download(self):
        request = Request(self.getURL('file'))
        d = self.download_request(request)
        d.addCallback(lambda r: r.body)
        d.addCallback(self.assertEquals, '0123456789')
        return d

    def test_download_head(self):
        request = Request(self.getURL('file'), method='HEAD')
        d = self.download_request(request)
        d.addCallback(lambda r: r.body)
        d.addCallback(self.assertEquals, '')
        return d

    def test_redirect_status(self):
        request = Request(self.getURL('redirect'))
        d = self.download_request(request)
        d.addCallback(lambda r: r.status)
        d.addCallback(self.assertEquals, 302)
        return d

    def test_redirect_status_head(self):
        request = Request(self.getURL('redirect'), method='HEAD')
        d = self.download_request(request)
        d.addCallback(lambda r: r.status)
        d.addCallback(self.assertEquals, 302)
        return d

    def test_host_header_not_in_request_headers(self):
        def _test(response):
            self.assertEquals(response.body, '127.0.0.1:%d' % self.portno)
            self.assertEquals(request.headers, {})

        request = Request(self.getURL('host'))
        d = self.download_request(request)
        d.addCallback(_test)
        return d

    def test_host_header_seted_in_request_headers(self):
        def _test(response):
            self.assertEquals(response.body, 'example.com')
            self.assertEquals(request.headers.get('Host'), 'example.com')

        request = Request(self.getURL('host'), headers={'Host': 'example.com'})
        d = self.download_request(request)
        d.addCallback(_test)
        return d

    def test_payload(self):
        body = '1' * 100  # PayloadResource requires body length to be 100
        request = Request(self.getURL('payload'), method='POST', body=body)
        d = self.download_request(request)
        d.addCallback(lambda r: r.body)
        d.addCallback(self.assertEquals, body)
        return d


class UriResource(resource.Resource):
    '''Return the full uri that was requested'''

    def getChild(self, path, request):
        return self

    def render(self, request):
        return request.uri


class HttpProxyTest(unittest.TestCase):

    def setUp(self):
        site = server.Site(UriResource(), timeout=None)
        wrapper = WrappingFactory(site)
        self.port = reactor.listenTCP(0, wrapper, interface='127.0.0.1')
        self.portno = self.port.getHost().port
        self.download_request = HttpDownloadHandler(Settings()).download_request

    def tearDown(self):
        return self.port.stopListening()

    def getURL(self, path):
        return 'http://127.0.0.1:%d/%s' % (self.portno, path)

    def test_download_with_proxy(self):
        def _test(response):
            self.assertEquals(response.status, 200)
            self.assertEquals(response.url, request.url)
            self.assertEquals(response.body, 'https://example.com/')

        http_proxy = self.getURL('')
        request = Request('https://example.com', proxy=http_proxy)
        return self.download_request(request).addCallback(_test)

    def test_download_without_proxy(self):
        def _test(response):
            self.assertEquals(response.status, 200)
            self.assertEquals(response.url, request.url)
            self.assertEquals(response.body, '/path/to/resource')

        request = Request(self.getURL('path/to/resource'))
        return self.download_request(request).addCallback(_test)


class NonConfiguredHandler(object):
    def __init__(self, settings):
        raise NotConfigured()


class GeneralTest(unittest.TestCase):

    def setUp(self):
        self.settings = Settings({
            'DOWNLOAD_HANDLERS': {
                'file': 'crawlmi.core.handlers.FileDownloadHandler',
                'http': 'crawlmi.core.handlers.HttpDownloadHandler',
                'https': 'crawlmi.tests.test_downloader_handlers.NonConfiguredHandler',
            }
        })
        self.handler = GeneralHandler(self.settings)

    def test_init(self):
        self.assertIsInstance(self.handler._handlers['file'], FileDownloadHandler)
        self.assertIsInstance(self.handler._handlers['http'], HttpDownloadHandler)
        self.assertIn('https', self.handler._not_configured)

    def test_get_handler(self):
        h = self.handler._get_handler(Request('file:///etc/fstab'))
        self.assertIsInstance(h, FileDownloadHandler)
        h = self.handler._get_handler(Request('http://www.github.com/'))
        self.assertIsInstance(h, HttpDownloadHandler)
        self.assertRaises(NotSupported, self.handler._get_handler,
                          Request('https://www.githib.com/'))
