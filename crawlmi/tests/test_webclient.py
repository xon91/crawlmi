import os

from twisted.internet import reactor, defer
from twisted.protocols.policies import WrappingFactory
from twisted.python.filepath import FilePath
from twisted.test.proto_helpers import StringTransport
from twisted.trial import unittest
from twisted.web import server, static, util
from twisted.web.test.test_webclient import (ForeverTakingResource,
        ErrorResource, NoLengthResource, HostHeaderResource,
        PayloadResource, BrokenDownloadResource)

from crawlmi.core.webclient import (BadHttpHeaderError, CrawlmiHTTPClient,
                                    CrawlmiHTPPClientFactory, _parse_url_args)
from crawlmi.exceptions import DownloadSizeError
from crawlmi.http import Headers, Request


class ParseUrlTest(unittest.TestCase):
    def _parse(self, url):
        f = CrawlmiHTPPClientFactory(Request(url=url))
        return (f.scheme, f.netloc, f.host, f.port, f.path)

    def test_parse(self):
        lip = '127.0.0.1'
        tests = [
            ('http://127.0.0.1?c=v&c2=v2#fragment',     ('http', lip, lip, 80, '/?c=v&c2=v2')),
            ('http://127.0.0.1/?c=v&c2=v2#fragment',    ('http', lip, lip, 80, '/?c=v&c2=v2')),
            ('http://127.0.0.1/foo?c=v&c2=v2#frag',     ('http', lip, lip, 80, '/foo?c=v&c2=v2')),
            ('http://127.0.0.1:100?c=v&c2=v2#fragment', ('http', lip + ':100', lip, 100, '/?c=v&c2=v2')),
            ('http://127.0.0.1:100/?c=v&c2=v2#frag',    ('http', lip + ':100', lip, 100, '/?c=v&c2=v2')),
            ('http://127.0.0.1:100/foo?c=v&c2=v2#frag', ('http', lip + ':100', lip, 100, '/foo?c=v&c2=v2')),

            ('http://127.0.0.1',              ('http', lip, lip, 80, '/')),
            ('http://127.0.0.1/',             ('http', lip, lip, 80, '/')),
            ('http://127.0.0.1/foo',          ('http', lip, lip, 80, '/foo')),
            ('http://127.0.0.1?param=value',  ('http', lip, lip, 80, '/?param=value')),
            ('http://127.0.0.1/?param=value', ('http', lip, lip, 80, '/?param=value')),
            ('http://127.0.0.1:12345/foo',    ('http', lip + ':12345', lip, 12345, '/foo')),
            ('http://spam:12345/foo',         ('http', 'spam:12345', 'spam', 12345, '/foo')),
            ('http://spam.test.org/foo',      ('http', 'spam.test.org', 'spam.test.org', 80, '/foo')),

            ('https://127.0.0.1/foo',         ('https', lip, lip, 443, '/foo')),
            ('https://127.0.0.1/?param=value', ('https', lip, lip, 443, '/?param=value')),
            ('https://127.0.0.1:12345/',      ('https', lip + ':12345', lip, 12345, '/')),

            ('http://crawlmitest.org/foo ',    ('http', 'crawlmitest.org', 'crawlmitest.org', 80, '/foo')),
            ('http://egg:7890 ',              ('http', 'egg:7890', 'egg', 7890, '/')),
        ]

        f = CrawlmiHTPPClientFactory(Request(url='http://github.com/'))
        for url, test in tests:
            self.assertEqual(_parse_url_args(url), test, url)


class HTTPPageGetterTest(unittest.TestCase):
    def _test(self, factory, testvalue):
        transport = StringTransport()
        protocol = CrawlmiHTTPClient()
        protocol.factory = factory
        protocol.makeConnection(transport)
        self.assertEqual(transport.value(), testvalue)

    def test_early_headers(self):
        # basic test stolen from twisted HTTPageGetter
        factory = CrawlmiHTPPClientFactory(Request(
            url='http://foo/bar',
            body='some data',
            headers={
                'Host': 'example.net',
                'User-Agent': 'fooble',
                'Cookie': 'blah blah',
                'Content-Length': '12981',
                'Useful': 'value'}))

        self._test(factory,
            'GET /bar HTTP/1.0\r\n'
            'Content-Length: 9\r\n'
            'Useful: value\r\n'
            'Connection: close\r\n'
            'User-Agent: fooble\r\n'
            'Host: example.net\r\n'
            'Cookie: blah blah\r\n'
            '\r\n'
            'some data')

        # test minimal sent headers
        factory = CrawlmiHTPPClientFactory(Request('http://foo/bar'))
        self._test(factory,
            'GET /bar HTTP/1.0\r\n'
            'Host: foo\r\n'
            '\r\n')

        # test a simple POST with body and content-type
        factory = CrawlmiHTPPClientFactory(Request(
            method='POST',
            url='http://foo/bar',
            body='name=value',
            headers={'Content-Type': 'application/x-www-form-urlencoded'}))

        self._test(factory,
            'POST /bar HTTP/1.0\r\n'
            'Host: foo\r\n'
            'Connection: close\r\n'
            'Content-Type: application/x-www-form-urlencoded\r\n'
            'Content-Length: 10\r\n'
            '\r\n'
            'name=value')

        # test with single and multivalued headers
        factory = CrawlmiHTPPClientFactory(Request(
            url='http://foo/bar',
            headers={
                'X-Meta-Single': 'single',
                'X-Meta-Multivalued': ['value1', 'value2']}))

        self._test(factory,
            'GET /bar HTTP/1.0\r\n'
            'Host: foo\r\n'
            'X-Meta-Multivalued: value1\r\n'
            'X-Meta-Multivalued: value2\r\n'
            'X-Meta-Single: single\r\n'
            '\r\n')

        # same test with single and multivalued headers but using Headers class
        factory = CrawlmiHTPPClientFactory(Request(
            url='http://foo/bar',
            headers=Headers({
                'X-Meta-Single': 'single',
                'X-Meta-Multivalued': ['value1', 'value2']})))

        self._test(factory,
            'GET /bar HTTP/1.0\r\n'
            'Host: foo\r\n'
            'X-Meta-Multivalued: value1\r\n'
            'X-Meta-Multivalued: value2\r\n'
            'X-Meta-Single: single\r\n'
            '\r\n')

    def test_non_standard_line_endings(self):
        factory = CrawlmiHTPPClientFactory(Request(url='http://foo/bar'))
        protocol = CrawlmiHTTPClient()
        protocol.factory = factory
        protocol.headers = Headers()
        protocol.dataReceived('HTTP/1.0 200 OK\n')
        protocol.dataReceived('Hello: World\n')
        protocol.dataReceived('Foo: Bar\n')
        protocol.dataReceived('\n')
        self.assertEqual(protocol.headers,
            Headers({'Hello': ['World'], 'Foo': ['Bar']}))

    def test_invalid_headers(self):
        transport = StringTransport()
        factory = CrawlmiHTPPClientFactory(Request(url='http://foo/bar'))
        protocol = CrawlmiHTTPClient()
        protocol.factory = factory
        protocol.makeConnection(transport)
        protocol.headers = Headers()
        protocol.dataReceived('HTTP/1.0 200 OK\r\n')
        protocol.dataReceived('Hello World\r\n')
        protocol.dataReceived('Foo: Bar\r\n')
        protocol.dataReceived('\r\n')
        protocol.handleResponse('')
        return self.assertFailure(factory.deferred, BadHttpHeaderError)

    def test_invalid_status(self):
        transport = StringTransport()
        factory = CrawlmiHTPPClientFactory(Request(url='http://foo/bar'))
        protocol = CrawlmiHTTPClient()
        protocol.factory = factory
        protocol.makeConnection(transport)
        protocol.headers = Headers()
        protocol.dataReceived('HTTP/1.0 BUG OK\r\n')
        protocol.dataReceived('Hello: World\r\n')
        protocol.dataReceived('Foo: Bar\r\n')
        protocol.dataReceived('\r\n')
        protocol.handleResponse('')
        return self.assertFailure(factory.deferred, BadHttpHeaderError)


class WebClientTest(unittest.TestCase):
    def _listen(self, site):
        return reactor.listenTCP(0, site, interface='127.0.0.1')

    def setUp(self):
        name = self.mktemp()
        os.mkdir(name)
        FilePath(name).child('file').setContent('0123456789')
        r = static.File(name)
        r.putChild('redirect', util.Redirect('/file'))
        r.putChild('wait', ForeverTakingResource())
        r.putChild('error', ErrorResource())
        r.putChild('nolength', NoLengthResource())
        r.putChild('host', HostHeaderResource())
        r.putChild('payload', PayloadResource())
        r.putChild('broken', BrokenDownloadResource())
        self.site = server.Site(r, timeout=None)
        self.wrapper = WrappingFactory(self.site)
        self.port = self._listen(self.wrapper)
        self.portno = self.port.getHost().port

    def tearDown(self):
        return self.port.stopListening()

    def get_url(self, path):
        return 'http://127.0.0.1:%d/%s' % (self.portno, path)

    def get_page(self, url, contextFactory=None, *args, **kwargs):
        '''Adapted version of twisted.web.client.getPage'''
        def _clientfactory(*args, **kwargs):
            timeout = kwargs.pop('timeout', 0)
            download_size = kwargs.pop('download_size', 0)
            f = CrawlmiHTPPClientFactory(Request(*args, **kwargs),
                timeout=timeout, download_size=download_size)
            f.deferred.addCallback(lambda r: r.body)
            return f
        from twisted.web.client import _makeGetterFactory
        return _makeGetterFactory(url, _clientfactory,
            contextFactory=contextFactory, *args, **kwargs).deferred

    def test_payload(self):
        s = '0123456789' * 10
        return self.get_page(self.get_url('payload'), body=s).addCallback(self.assertEquals, s)

    def test_size_limit(self):
        s = 'x' * 100
        return self.assertFailure(
            self.get_page(self.get_url('payload'), body=s, download_size=10),
            DownloadSizeError)

    def test_host_header(self):
        # if we pass Host header explicitly, it should be used, otherwise
        # it should extract from url
        return defer.gatherResults([
            self.get_page(self.get_url('host')).addCallback(
                self.assertEquals, '127.0.0.1:%d' % self.portno),
            self.get_page(self.get_url('host'),
                headers={'Host': 'www.example.com'}).addCallback(
                    self.assertEquals, 'www.example.com')])

    def test_get_page(self):
        '''get_page returns a Deferred which is called back with
        the body of the response if the default method GET is used.
        '''
        d = self.get_page(self.get_url('file'))
        d.addCallback(self.assertEquals, '0123456789')
        return d

    def test_get_page_head(self):
        '''
        get_page returns a Deferred which is called back with
        the empty string if the method is HEAD and there is a successful
        response code.
        '''
        def _getPage(method):
            return self.get_page(self.get_url('file'), method=method)
        return defer.gatherResults([
            _getPage('head').addCallback(self.assertEqual, ''),
            _getPage('HEAD').addCallback(self.assertEqual, '')])

    def test_timeout_not_triggering(self):
        '''
        When a non-zero timeout is passed to get_page and the page is
        retrieved before the timeout period elapses, the Deferred is
        called back with the contents of the page.
        '''
        d = self.get_page(self.get_url('host'), timeout=100)
        d.addCallback(self.assertEquals, '127.0.0.1:%d' % self.portno)
        return d

    def test_timeout_triggering(self):
        '''
        When a non-zero timeout is passed to get_page and that many
        seconds elapse before the server responds to the request. the
        Deferred is errbacked with a error.TimeoutError.
        '''
        def cleanup(passthrough):
            # Clean up the server which is hanging around not doing
            # anything.
            connected = self.wrapper.protocols.keys()
            # There might be nothing here if the server managed to already see
            # that the connection was lost.
            if connected:
                connected[0].transport.loseConnection()
            return passthrough

        finished = self.assertFailure(
            self.get_page(self.get_url('wait'), timeout=0.000001),
            defer.TimeoutError)
        finished.addBoth(cleanup)
        return finished

    def test_not_found(self):
        def _cb_no_such_file(page_data):
            self.assert_('404 - No Such Resource' in page_data)
        return self.get_page(self.get_url('notsuchfile')).addCallback(_cb_no_such_file)

    def test_factory_info(self):
        def _cbFactoryInfo(ingnored_result, factory):
            self.assertEquals(factory.status, 200)
            self.assert_(factory.version.startswith('HTTP/'))
            self.assertEquals(factory.message, 'OK')
            self.assertEquals(factory.response_headers['content-length'], '10')

        url = self.get_url('file')
        factory = CrawlmiHTPPClientFactory(Request(url))
        scheme, netloc, host, port, path = _parse_url_args(url)
        reactor.connectTCP(host, port, factory)
        return factory.deferred.addCallback(_cbFactoryInfo, factory)

    def test_redirect(self):
        def _cb_redirect(pageData):
            self.assertEquals(pageData,
                '\n<html>\n    <head>\n        '
                '<meta http-equiv="refresh" content="0;URL=/file">\n'
                '    </head>\n    <body bgcolor="#FFFFFF" text="#000000">\n    '
                '<a href="/file">click here</a>\n    </body>\n</html>\n')
        return self.get_page(self.get_url('redirect')).addCallback(_cb_redirect)
