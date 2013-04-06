from twisted.trial import unittest

from crawlmi.http import (Headers, Response, TextResponse, XmlResponse,
                          HtmlResponse)
from crawlmi.http.response.factory import (from_mime_type, from_filename,
        from_content_disposition, from_content_type, from_body, from_headers,
        from_args, _mime_types)


class FactoryTest(unittest.TestCase):
    def test_from_filename(self):
        mappings = [
            ('data.bin', Response),
            ('file.txt', TextResponse),
            ('file.xml.gz', Response),
            ('file.xml', XmlResponse),
            ('file.html', HtmlResponse),
            ('file.unknownext', Response),
        ]
        for source, cls in mappings:
            retcls = from_filename(source)
            self.assertIs(retcls, cls, 'Expected: %s  Received: %s' % (cls.__name__, retcls.__name__))

    def test_from_content_disposition(self):
        mappings = [
            ('attachment; filename="data.xml"', XmlResponse),
            ('attachment; filename=data.xml', XmlResponse),
        ]
        for source, cls in mappings:
            retcls = from_content_disposition(source)
            self.assertIs(retcls, cls, 'Expected: %s  Received: %s' % (cls.__name__, retcls.__name__))

    def test_from_content_type(self):
        mappings = [
            ('text/html; charset=UTF-8', HtmlResponse),
            ('text/xml; charset=UTF-8', XmlResponse),
            ('application/xhtml+xml; charset=UTF-8', HtmlResponse),
            ('application/vnd.wap.xhtml+xml; charset=utf-8', HtmlResponse),
            ('application/xml; charset=UTF-8', XmlResponse),
            ('application/octet-stream', Response),
        ]
        for source, cls in mappings:
            retcls = from_content_type(source)
            self.assertIs(retcls, cls, 'Expected: %s  Received: %s' % (cls.__name__, retcls.__name__))

    def test_from_body(self):
        mappings = [
            ('\x03\x02\xdf\xdd\x23', Response),
            ('Some plain text\ndata with tabs\t and null bytes\0', TextResponse),
            ('<html><head><title>Hello</title></head>', HtmlResponse),
            ('<?xml version="1.0" encoding="utf-8"', XmlResponse),
        ]
        for source, cls in mappings:
            retcls = from_body(source)
            self.assertIs(retcls, cls, 'Expected: %s  Received: %s' % (cls.__name__, retcls.__name__))

    def test_from_headers(self):
        mappings = [
            ({'Content-Type': ['text/html; charset=utf-8']}, HtmlResponse),
            ({'Content-Type': ['application/octet-stream'], 'Content-Disposition': ['attachment; filename=data.txt']}, TextResponse),
            ({'Content-Type': ['text/html; charset=utf-8'], 'Content-Encoding': ['gzip']}, Response),
        ]
        for source, cls in mappings:
            source = Headers(source)
            retcls = from_headers(source)
            self.assertIs(retcls, cls, 'Expected: %s  Received: %s' % (cls.__name__, retcls.__name__))

    def test_from_args(self):
        mappings = [
            ({'url': 'http://www.example.com/data.csv'}, TextResponse),
            # headers takes precedence over url
            ({'headers': Headers({'Content-Type': ['text/html; charset=utf-8']}), 'url': 'http://www.example.com/item/'}, HtmlResponse),
            ({'headers': Headers({'Content-Disposition': ['attachment; filename="data.xml.gz"']}), 'url': 'http://www.example.com/page/'}, Response),


        ]
        for source, cls in mappings:
            retcls = from_args(**source)
            self.assertIs(retcls, cls, 'Expected: %s  Received: %s' % (cls.__name__, retcls.__name__))

    def test_custom_mime_types_loaded(self):
        self.assertEqual(_mime_types.guess_type('x.crawlmitest')[0], 'x-crawlmi/test')
