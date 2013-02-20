from twisted.trial import unittest

from crawlmi.http.headers import Headers
from crawlmi.http.request import Request
from crawlmi.http.response import Response


class ResponseTest(unittest.TestCase):

    def test_init(self):
        self.assertRaises(Exception, Response)
        self.assertIsInstance(Response(url='http://github.com/'), Response)

        self.assertIsInstance(Response(url='http://github.com/', body=''), Response)
        self.assertIsInstance(Response(url='http://github.com/', body='something'), Response)
        r = Response(url='http://github.com/', body=None)
        self.assertIsInstance(r.url, str)
        self.assertEqual(r.body, '')
        self.assertEqual(r.status, 200)
        self.assertIsInstance(r.headers, Headers)
        self.assertEqual(r.headers, {})

        headers = {'caca': 'coco'}
        body = 'a body'
        r = Response('http://www.example.com', headers=headers, body=body)
        self.assertIsInstance(r.headers, Headers)
        self.assertIsNot(r.headers, headers)
        self.assertEqual(r.headers['caca'], 'coco')
        r = Response('http://www.example.com', status=301)
        self.assertEqual(r.status, 301)
        r = Response('http://www.example.com', status='301')
        self.assertEqual(r.status, 301)
        self.assertRaises(ValueError, Response, 'http://example.com', status='lala200')

    def test_properties(self):
        r = Response('', body='hey')

        def set_body():
            r.body = ''
        self.assertEqual(r.body, 'hey')
        self.assertRaises(AttributeError, set_body)

    def test_request(self):
        req = Request(url='http://github.com', meta={'a': 'b'})
        req.history = ['a', 'b']
        r = Response(url='', request=req)
        self.assertIs(r.request, req)
        self.assertIs(r.meta, req.meta)
        self.assertIs(r.history, req.history)
        self.assertIs(r.original_url, req.original_url)
        r = Response(url='')
        from crawlmi.http.response.response import _no_request_error
        self.assertRaisesRegexp(AttributeError, _no_request_error, lambda: r.meta)
        self.assertRaisesRegexp(AttributeError, _no_request_error, lambda: r.history)
        self.assertRaisesRegexp(AttributeError, _no_request_error, lambda: r.original_url)

    def test_copy(self):
        req = Request('http://gh.com/')
        r1 = Response(url='http://hey.com/', status=201, headers={'a': 'b'},
                      body='hey', request=req)
        r2 = r1.copy()

        self.assertEqual(r1.url, r2.url)
        self.assertEqual(r1.status, r2.status)
        self.assertEqual(r1.body, r2.body)
        self.assertIs(r1.request, r2.request)
        self.assertIsInstance(r2.headers, Headers)
        self.assertDictEqual(r1.headers, r2.headers)

    def test_copy_inherited_classes(self):
        class CustomResponse(Response):
            pass

        r1 = CustomResponse('')
        r2 = r1.copy()
        self.assertIsInstance(r2, CustomResponse)
