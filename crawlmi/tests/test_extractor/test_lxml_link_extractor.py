from twisted.trial import unittest

from crawlmi.extractor import Link, LxmlLinkExtractor
from crawlmi.http import HtmlResponse
from crawlmi.tests import get_testdata


class LxmlLinkExtractorTest(unittest.TestCase):
    def setUp(self):
        body = get_testdata('link_extractor', 'sgml_linkextractor.html')
        self.response = HtmlResponse(url='http://example.com/index', body=body)

    def test_basic(self):
        html = '''<html><head><title>Page title<title>
        <body><p><a href="item/12.html">Item 12</a></p>
        <p><a href="/about.html">About us</a></p>
        <img src="/logo.png" alt="Company logo (not a link)" />
        <p><a href="../othercat.html">Other category</a></p>
        <p><a href="/">&gt;&gt;</a></p>
        <p><a href="/" /></p>
        </body></html>'''
        response = HtmlResponse('http://example.org/somepage/index.html', body=html)

        lx = LxmlLinkExtractor(unique=False)
        self.assertListEqual(lx.extract_links(response),
                             [Link(url='http://example.org/somepage/item/12.html', text='Item 12'),
                              Link(url='http://example.org/about.html', text='About us'),
                              Link(url='http://example.org/othercat.html', text='Other category'),
                              Link(url='http://example.org/', text='>>'),
                              Link(url='http://example.org/', text='')])

    def test_base_url(self):
        html = '''<html><head><title>Page title<title><base href="http://otherdomain.com/base/" />
        <body><p><a href="item/12.html">Item 12</a></p>
        </body></html>'''
        response = HtmlResponse('http://example.org/somepage/index.html', body=html)

        lx = LxmlLinkExtractor(unique=False)
        self.assertEqual(lx.extract_links(response),
                         [Link(url='http://otherdomain.com/base/item/12.html', text='Item 12')])

        # base url is an absolute path and relative to host
        html = '''<html><head><title>Page title<title><base href="/" />
        <body><p><a href="item/12.html">Item 12</a></p></body></html>'''
        response = HtmlResponse('https://example.org/somepage/index.html', body=html)
        self.assertEqual(lx.extract_links(response),
                         [Link(url='https://example.org/item/12.html', text='Item 12')])

        # base url has no scheme
        html = '''<html><head><title>Page title<title><base href="//noschemedomain.com/path/to/" />
        <body><p><a href="item/12.html">Item 12</a></p></body></html>'''
        response = HtmlResponse('https://example.org/somepage/index.html', body=html)
        self.assertEqual(lx.extract_links(response),
                         [Link(url='https://noschemedomain.com/path/to/item/12.html', text='Item 12')])

    def test_link_text_wrong_encoding(self):
        html = '''<body><p><a href="item/12.html">Wrong: \xed</a></p></body></html>'''
        response = HtmlResponse('http://www.example.com', body=html, encoding='utf-8')
        lx = LxmlLinkExtractor(unique=False)
        self.assertEqual(lx.extract_links(response), [
            Link(url='http://www.example.com/item/12.html', text=u'Wrong: \ufffd'),
        ])

    def test_invalid(self):
        # parser shouldn't fail or anything
        html = '''<?xml version="1.0" encoding="utf-8"?>
            <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
            <html xmlns="http://www.w3.org/1999/xhtml" lang="cs">
            <body>
            </body>
            </html>'''
        response = HtmlResponse('http://www.example.com', body=html, encoding='utf-8')
        lx = LxmlLinkExtractor(unique=False)
        self.assertEqual(lx.extract_links(response), [])

    def test_extraction_encoding(self):
        body = get_testdata('link_extractor', 'linkextractor_noenc.html')
        response_utf8 = HtmlResponse(url='http://example.com/utf8', body=body, headers={'Content-Type': ['text/html; charset=utf-8']})
        response_noenc = HtmlResponse(url='http://example.com/noenc', body=body)
        body = get_testdata('link_extractor', 'linkextractor_latin1.html')
        response_latin1 = HtmlResponse(url='http://example.com/latin1', body=body)

        lx = LxmlLinkExtractor(unique=False)
        self.assertEqual(lx.extract_links(response_utf8), [
            Link(url='http://example.com/sample_%C3%B1.html', text=''),
            Link(url='http://example.com/sample_%E2%82%AC.html', text='sample \xe2\x82\xac text'.decode('utf-8')),
        ])

        self.assertEqual(lx.extract_links(response_noenc), [
            Link(url='http://example.com/sample_%C3%B1.html', text=''),
            Link(url='http://example.com/sample_%E2%82%AC.html', text='sample \xe2\x82\xac text'.decode('utf-8')),
        ])

        self.assertEqual(lx.extract_links(response_latin1), [
            Link(url='http://example.com/sample_%F1.html', text=''),
            Link(url='http://example.com/sample_%E1.html', text='sample \xe1 text'.decode('latin1')),
        ])

    def test_empty_body(self):
        lx = LxmlLinkExtractor()
        response = HtmlResponse('http://www.example.com')
        self.assertEqual(lx.extract_links(response), [])

    def test_urls_type(self):
        '''Test that the resulting urls are regular strings and not a unicode objects.
        '''
        lx = LxmlLinkExtractor()
        self.assertTrue(all(isinstance(link.url, str) for link in lx.extract_links(self.response)))

    def test_extraction(self):
        '''Test the extractor's behaviour among different situations.
        '''
        lx = LxmlLinkExtractor()
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
            Link(url='http://example.com/sample3.html', text=u'sample 3 text'),
            Link(url='http://www.google.com/something', text=u''),
        ])

        lx = LxmlLinkExtractor(allow=('sample', ))
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
            Link(url='http://example.com/sample3.html', text=u'sample 3 text'),
        ])

        lx = LxmlLinkExtractor(allow=('sample', ), unique=False)
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
            Link(url='http://example.com/sample3.html', text=u'sample 3 text'),
            Link(url='http://example.com/sample3.html', text=u'sample 3 repetition'),
        ])

        lx = LxmlLinkExtractor(allow=('sample', ))
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
            Link(url='http://example.com/sample3.html', text=u'sample 3 text'),
        ])

        lx = LxmlLinkExtractor(allow=('sample', ), deny=('3', ))
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
        ])

        lx = LxmlLinkExtractor(allow_domains=('google.com', ))
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://www.google.com/something', text=u''),
        ])

    def test_extraction_using_single_values(self):
        '''Test the extractor's behaviour among different situations.
        '''
        lx = LxmlLinkExtractor(allow='sample')
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
            Link(url='http://example.com/sample3.html', text=u'sample 3 text'),
        ])

        lx = LxmlLinkExtractor(allow='sample', deny='3')
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://example.com/sample1.html', text=u''),
            Link(url='http://example.com/sample2.html', text=u'sample 2'),
        ])

        lx = LxmlLinkExtractor(allow_domains='google.com')
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://www.google.com/something', text=u''),
        ])

        lx = LxmlLinkExtractor(deny_domains='example.com')
        self.assertEqual([link for link in lx.extract_links(self.response)], [
            Link(url='http://www.google.com/something', text=u''),
        ])

    def test_url_allowed(self):
        url1 = 'http://lotsofstuff.com/stuff1/index'
        url2 = 'http://evenmorestuff.com/uglystuff/index'

        lx = LxmlLinkExtractor(allow=(r'stuff1', ))
        self.assertEqual(lx.url_allowed(url1), True)
        self.assertEqual(lx.url_allowed(url2), False)

        lx = LxmlLinkExtractor(deny=(r'uglystuff', ))
        self.assertEqual(lx.url_allowed(url1), True)
        self.assertEqual(lx.url_allowed(url2), False)

        lx = LxmlLinkExtractor(allow_domains=('evenmorestuff.com', ))
        self.assertEqual(lx.url_allowed(url1), False)
        self.assertEqual(lx.url_allowed(url2), True)

        lx = LxmlLinkExtractor(deny_domains=('lotsofstuff.com', ))
        self.assertEqual(lx.url_allowed(url1), False)
        self.assertEqual(lx.url_allowed(url2), True)

        lx = LxmlLinkExtractor(allow=('blah1',), deny=('blah2',),
                               allow_domains=('blah1.com',),
                               deny_domains=('blah2.com',))
        self.assertEqual(lx.url_allowed('http://blah1.com/blah1'), True)
        self.assertEqual(lx.url_allowed('http://blah1.com/blah2'), False)
        self.assertEqual(lx.url_allowed('http://blah2.com/blah1'), False)
        self.assertEqual(lx.url_allowed('http://blah2.com/blah2'), False)

    def test_encoded_url(self):
        body = '''<html><body><div><a href="?page=2">BinB</a></body></html>'''
        response = HtmlResponse("http://known.fm/AC%2FDC/", body=body, encoding='utf8')
        lx = LxmlLinkExtractor()
        self.assertEqual(lx.extract_links(response), [
            Link(url='http://known.fm/AC%2FDC/?page=2', text=u'BinB'),
        ])

    def test_deny_extensions(self):
        html = '''<a href="page.html">asd</a> and <a href="photo.jpg">'''
        response = HtmlResponse('http://example.org/', body=html)
        lx = LxmlLinkExtractor()
        self.assertEqual(lx.extract_links(response), [
            Link(url='http://example.org/page.html', text=u'asd'),
        ])

    def test_process_links(self):
        def _process(link):
            if link.url.endswith('othercat.html'):
                return None
            else:
                link.url = 'http://gogo.com/'
                return link

        html = '''<html><head><title>Page title<title>
        <p><a href="../othercat.html">Other category</a></p>
        <p><a href="/">&gt;&gt;</a></p>
        <p><a href="/">mimi</a></p>
        <p><a href="/hello">mimino</a></p>
        </body></html>'''
        response = HtmlResponse('http://example.org/', body=html)
        lx = LxmlLinkExtractor()
        self.assertEqual(lx.extract_links(response, process_links=_process), [
            Link(url='http://gogo.com/', text=u'>>')
        ])
