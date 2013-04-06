from twisted.trial import unittest

from crawlmi.http import Request
from crawlmi.utils.request import request_http_repr


class UtilsRequestTest(unittest.TestCase):
    def test_request_http_repr(self):
        r1 = Request('http://www.example.com')
        self.assertEqual(request_http_repr(r1), 'GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n')

        r1 = Request('http://www.example.com/some/page.html?arg=1')
        self.assertEqual(request_http_repr(r1), 'GET /some/page.html?arg=1 HTTP/1.1\r\nHost: www.example.com\r\n\r\n')

        r1 = Request('http://www.example.com', method='POST', headers={'Content-type': 'text/html'}, body='Some body')
        self.assertEqual(request_http_repr(r1), 'POST / HTTP/1.1\r\nHost: www.example.com\r\nContent-Type: text/html\r\n\r\nSome body')
