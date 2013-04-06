from twisted.trial import unittest

from crawlmi.http.request import Request
from crawlmi.http.response import Response
from crawlmi.middleware.pipelines.redirect import Redirect
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
