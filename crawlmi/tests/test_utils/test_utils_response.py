import os
import urlparse

from twisted.trial import unittest

from crawlmi.http import Response, HtmlResponse
from crawlmi.utils.response import (open_in_browser, response_http_repr,
                                    get_meta_refresh)


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

    def test_get_meta_refresh(self):
        url = 'http://example.org'
        body = '''
            <html>
                <head><title>Dummy</title><meta http-equiv="refresh" content="5;url=http://example.org/newpage" /></head>
                <body>blahablsdfsal&amp;</body>
            </html>'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (5, 'http://example.org/newpage'))

        # refresh without url should return (None, None)
        body = '''<meta http-equiv="refresh" content="5" />'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (None, None))

        body = '''<meta http-equiv="refresh" content="5;
            url=http://example.org/newpage" /></head>'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (5, 'http://example.org/newpage'))

        # meta refresh in multiple lines
        body = '''<html><head>
<META
HTTP-EQUIV="Refresh"
CONTENT="1; URL=http://example.org/newpage">'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (1, 'http://example.org/newpage'))

        # entities in the redirect url
        body = '''<meta http-equiv="refresh" content="3; url=&#39;http://www.example.com/other&#39;">'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (3, 'http://www.example.com/other'))

        url = 'http://example.com/page/this.html'
        # relative redirects
        body = '''<meta http-equiv="refresh" content="3; url=other.html">'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (3, 'http://example.com/page/other.html'))

        # non-standard encodings (utf-16)
        url = 'http://example.com'
        body = '''<meta http-equiv="refresh" content="3; url=http://example.com/redirect">'''
        body = body.decode('ascii').encode('utf-16')
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body, encoding='utf-16')),
            (3, 'http://example.com/%FF%FEh%00t%00t%00p%00:%00/%00/%00e%00x%00a%00m%00p%00l%00e%00.%00c%00o%00m%00/%00r%00e%00d%00i%00r%00e%00c%00t%00'))

        # non-ascii chars in the url (utf8 - default)
        body = '''<meta http-equiv="refresh" content="3; url=http://example.com/to\xc2\xa3">'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (3, 'http://example.com/to%C2%A3'))

        # non-ascii chars in the url (latin1)
        body = '''<meta http-equiv="refresh" content="3; url=http://example.com/to\xa3">'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body, encoding='latin1')), (3, 'http://example.com/to%A3'))

        # html commented meta refresh header must not directed
        body = '''<!--<meta http-equiv="refresh" content="3; url=http://example.com/">-->'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (None, None))

        # html comments must not interfere with uncommented meta refresh header
        body = '''<!-- commented --><meta http-equiv="refresh" content="3; url=http://example.com/">-->'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (3, 'http://example.com/'))

        # float refresh intervals
        body = '''<meta http-equiv="refresh" content=".1;URL=index.html" />'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (0.1, 'http://example.com/index.html'))

        body = '''<meta http-equiv="refresh" content="3.1;URL=index.html" />'''
        self.assertEqual(get_meta_refresh(HtmlResponse(url, body=body)), (3.1, 'http://example.com/index.html'))
