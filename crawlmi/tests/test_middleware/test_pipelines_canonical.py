from twisted.trial import unittest

from crawlmi.http import Request, Response, HtmlResponse
from crawlmi.middleware.pipelines.canonical import Canonical
from crawlmi.utils.test import get_engine


class CanonicalTest(unittest.TestCase):
    def setUp(self):
        self.mw = Canonical(get_engine())

    def test_nothing(self):
        body = '''<html><head></head><body></body></html>'''
        req = Request('http://a.com')
        rsp = HtmlResponse(req.url, body=body, request=req)
        rsp2 = self.mw.process_response(rsp)
        self.assertIs(rsp, rsp2)
        self.assertNotIn('canonical_url', rsp.meta)

    def test_tag(self):
        body = '''<html><head><link rel="canonical" href="%s" /></head></html>'''

        # absolute url
        req = Request('http://a.com/pom')
        rsp = HtmlResponse(req.url, body=body%'https://b.sk/hello', request=req)
        rsp2 = self.mw.process_response(rsp)
        self.assertIs(rsp, rsp2)
        self.assertEqual(rsp.meta['canonical_url'], 'https://b.sk/hello')

        # relative url
        req = Request('http://a.com/pom')
        rsp = HtmlResponse(req.url, body=body%'/hello/world', request=req)
        rsp2 = self.mw.process_response(rsp)
        self.assertIs(rsp, rsp2)
        self.assertEqual(rsp.meta['canonical_url'], 'http://a.com/hello/world')

    def test_header(self):
        # absolute url
        req = Request('http://a.com/pom')
        rsp = Response(req.url, headers={'Link': '<https://b.sk/hello>; rel="canonical"'}, request=req)
        rsp2 = self.mw.process_response(rsp)
        self.assertIs(rsp, rsp2)
        self.assertEqual(rsp.meta['canonical_url'], 'https://b.sk/hello')

        # relative url
        req = Request('http://a.com/pom')
        rsp = Response(req.url, headers={'Link': '</hello/world>; rel="canonical"'}, request=req)
        rsp2 = self.mw.process_response(rsp)
        self.assertIs(rsp, rsp2)
        self.assertEqual(rsp.meta['canonical_url'], 'http://a.com/hello/world')
