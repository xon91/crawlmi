from twisted.trial import unittest

from crawlmi.http import Request, Response, HtmlResponse
from crawlmi.middleware.pipelines.redirect import Redirect, MetaRefreshRedirect
from crawlmi.utils.test import get_engine


class RedirectTest(unittest.TestCase):
    def setUp(self):
        self.mw = Redirect(get_engine())

    def test_priority_adjust(self):
        req = Request('http://a.com')
        resp = Response('http://a.com', headers={'Location': 'http://a.com/redirected'}, status=301, request=req)
        req2 = self.mw.process_response(resp)
        assert req2.priority > req.priority

    def test_redirect_301(self):
        def _test(method):
            url = 'http://www.example.com/301'
            url2 = 'http://www.example.com/redirected'
            req = Request(url, method=method)
            resp = Response(url, headers={'Location': url2}, status=301, request=req)

            req2 = self.mw.process_response(resp)
            self.assertIsInstance(req2, Request)
            self.assertEqual(req2.url, url2)
            self.assertEqual(req2.method, method)

            # response without Location header but with status code is 3XX should be ignored
            del resp.headers['Location']
            self.assertIs(self.mw.process_response(resp), resp)

        _test('GET')
        _test('POST')
        _test('HEAD')

    def test_redirect_302(self):
        url = 'http://www.example.com/302'
        url2 = 'http://www.example.com/redirected2'
        req = Request(url, method='POST', body='test',
            headers={'Content-Type': 'text/plain', 'Content-length': '4'})
        resp = Response(url, headers={'Location': url2}, status=302, request=req)

        req2 = self.mw.process_response(resp)
        self.assertIsInstance(req2, Request)
        self.assertEqual(req2.url, url2)
        self.assertEqual(req2.method, 'GET')
        self.assertNotIn('Content-Type', req2.headers,
            'Content-Type header must not be present in redirected request')
        self.assertNotIn('Content-Length', req2.headers,
            'Content-Length header must not be present in redirected request')
        self.assertEqual(req2.body, '',
            'Redirected body must be empty, not `%s`' % req2.body)

        # response without Location header but with status code is 3XX should be ignored
        del resp.headers['Location']
        self.assertIs(self.mw.process_response(resp), resp)

    def test_redirect_302_head(self):
        url = 'http://www.example.com/302'
        url2 = 'http://www.example.com/redirected2'
        req = Request(url, method='HEAD')
        resp = Response(url, headers={'Location': url2}, status=302, request=req)

        req2 = self.mw.process_response(resp)
        self.assertIsInstance(req2, Request)
        self.assertEqual(req2.url, url2)
        self.assertEqual(req2.method, 'HEAD')

        # response without Location header but with status code is 3XX should be ignored
        del resp.headers['Location']
        self.assertIs(self.mw.process_response(resp), resp)

    def test_max_redirect_times(self):
        self.mw.max_redirect_times = 1
        req = Request('http://crawlmitest.org/302')
        resp = Response('http://crawlmitest.org/302', headers={'Location': '/redirected'}, status=302, request=req)

        req2 = self.mw.process_response(resp)
        self.assertIsInstance(req2, Request)
        self.assertListEqual(req2.history, ['http://crawlmitest.org/302'])
        resp2 = Response('http://crawlmitest.org/302', headers={'Location': '/redirected'}, status=302, request=req2)
        self.assertIsNone(self.mw.process_response(resp2))

    def test_redirect_urls(self):
        req1 = Request('http://crawlmitest.org/first')
        resp1 = Response('http://crawlmitest.org/first', headers={'Location': '/redirected'}, status=302, request=req1)
        req2 = self.mw.process_response(resp1)
        resp2 = Response('http://crawlmitest.org/redirected', headers={'Location': '/redirected2'}, status=302, request=req2)
        req3 = self.mw.process_response(resp2)

        self.assertEqual(req2.url, 'http://crawlmitest.org/redirected')
        self.assertListEqual(req2.history, ['http://crawlmitest.org/first'])
        self.assertEqual(req3.url, 'http://crawlmitest.org/redirected2')
        self.assertListEqual(req3.history, ['http://crawlmitest.org/first', 'http://crawlmitest.org/redirected'])


class MetaRefreshRedirectTest(unittest.TestCase):
    def setUp(self):
        self.mw = MetaRefreshRedirect(get_engine())

    def _body(self, interval=5, url='http://example.org/newpage'):
        return '''<html><head><meta http-equiv="refresh" content="%s;url=%s"/></head></html>''' % (interval, url)

    def test_priority_adjust(self):
        req = Request('http://a.com')
        rsp = HtmlResponse(req.url, body=self._body(), request=req)
        req2 = self.mw.process_response(rsp)
        self.assertTrue(req2.priority > req.priority)

    def test_meta_refresh(self):
        req = Request(url='http://example.org')
        rsp = HtmlResponse(req.url, body=self._body(), request=req)
        req2 = self.mw.process_response(rsp)
        self.assertIsInstance(req2, Request)
        self.assertEqual(req2.url, 'http://example.org/newpage')

    def test_meta_refresh_with_high_interval(self):
        # meta-refresh with high intervals don't trigger redirects
        req = Request(url='http://example.org')
        rsp = HtmlResponse(url='http://example.org', body=self._body(interval=1000), request=req)
        rsp2 = self.mw.process_response(rsp)
        self.assertIs(rsp, rsp2)

    def test_meta_refresh_trough_posted_request(self):
        req = Request(url='http://example.org', method='POST', body='test',
                      headers={'Content-Type': 'text/plain', 'Content-length': '4'})
        rsp = HtmlResponse(req.url, body=self._body(), request=req)
        req2 = self.mw.process_response(rsp)

        self.assertIsInstance(req2, Request)
        self.assertEqual(req2.url, 'http://example.org/newpage')
        self.assertEqual(req2.method, 'GET')
        self.assertNotIn('Content-Type', req2.headers,
            'Content-Type header must not be present in redirected request')
        self.assertNotIn('Content-Length', req2.headers,
            'Content-Length header must not be present in redirected request')
        self.assertNot(req2.body,
            'Redirected body must be empty, not `%s`' % req2.body)

    def test_max_redirect_times(self):
        self.mw.max_redirect_times = 1
        req = Request('http://test.org/max')
        rsp = HtmlResponse(req.url, body=self._body(), request=req)

        req = self.mw.process_response(rsp)
        self.assertIsInstance(req, Request)
        self.assertEqual(len(req.history), 1)
        rsp.request = req
        self.assertIsNone(self.mw.process_response(rsp))

    def test_redirect_urls(self):
        req1 = Request('http://test.org/first')
        rsp1 = HtmlResponse(req1.url, body=self._body(url='/redirected'), request=req1)
        req2 = self.mw.process_response(rsp1)
        self.assertIsInstance(req2, Request)
        rsp2 = HtmlResponse(req2.url, body=self._body(url='/redirected2'), request=req2)
        req3 = self.mw.process_response(rsp2)
        self.assertIsInstance(req3, Request)
        self.assertEqual(req2.url, 'http://test.org/redirected')
        self.assertListEqual(req2.history, ['http://test.org/first'])
        self.assertEqual(req3.url, 'http://test.org/redirected2')
        self.assertListEqual(req3.history, ['http://test.org/first', 'http://test.org/redirected'])
