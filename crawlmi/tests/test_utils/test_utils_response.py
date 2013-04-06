import os
import urlparse

from twisted.trial import unittest

from crawlmi.http import Response, HtmlResponse
from crawlmi.utils.response import open_in_browser, response_http_repr


class UtilsResponseTest(unittest.TestCase):
    def test_response_httprepr(self):
        r1 = Response('http://www.example.com')
        self.assertEqual(response_http_repr(r1), 'HTTP/1.1 200 OK\r\n\r\n')

        r1 = Response('http://www.example.com', status=404, headers={'Content-type': 'text/html'}, body='Some body')
        self.assertEqual(response_http_repr(r1), 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\nSome body')

        r1 = Response('http://www.example.com', status=6666, headers={'Content-type': 'text/html'}, body='Some body')
        self.assertEqual(response_http_repr(r1), 'HTTP/1.1 6666 \r\nContent-Type: text/html\r\n\r\nSome body')

    def test_open_in_browser(self):
        def browser_open(burl):
            path = urlparse.urlparse(burl).path
            if not os.path.exists(path):
                path = burl.replace('file://', '')
            bbody = open(path).read()
            self.assertIn('<base href="%s">' % url, bbody, '<base> tag not added')
            return True

        url = 'http:///www.example.com/some/page.html'
        body = '<html> <head> <title>test page</title> </head> <body>test body</body> </html>'
        response = HtmlResponse(url, body=body)
        self.assertTrue(open_in_browser(response, _openfunc=browser_open), 'Browser not called')
        self.assertRaises(TypeError, open_in_browser, Response(url, body=body))
