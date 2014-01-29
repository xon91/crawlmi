from twisted.trial import unittest

from crawlmi.http import Request, Response
from crawlmi.middleware.pipelines.cookies import Cookies
from crawlmi.utils.test import get_engine


class CookiesTest(unittest.TestCase):
    def setUp(self):
        self.mw = Cookies(get_engine())

    def test_basic(self):
        headers = {'Set-Cookie': 'C1=value1; path=/'}
        req = Request('http://test.org/')
        self.assertIs(req, self.mw.process_request(req))
        self.assertNotIn('Cookie', req.headers)

        res = Response('http://test.org/', request=req, headers=headers)
        self.assertIs(res, self.mw.process_response(res))

        req2 = Request('http://test.org/sub1/')
        self.assertIs(req2, self.mw.process_request(req2))
        self.assertEquals(req2.headers.get('Cookie'), 'C1=value1')

    def test_complex_cookies(self):
        # merge some cookies into jar
        cookies = [{'name': 'C1', 'value': 'value1', 'path': '/foo', 'domain': 'test.org'},
                {'name': 'C2', 'value': 'value2', 'path': '/bar', 'domain': 'test.org'},
                {'name': 'C3', 'value': 'value3', 'path': '/foo', 'domain': 'test.org'},
                {'name': 'C4', 'value': 'value4', 'path': '/foo', 'domain': 't.org'}]


        req = Request('http://test.org/', cookies=cookies)
        self.mw.process_request(req)

        # embed C1 and C3 for test.org/foo
        req = Request('http://test.org/foo')
        self.mw.process_request(req)
        self.assertIn(req.headers.get('Cookie'), ('C1=value1; C3=value3', 'C3=value3; C1=value1'))

        # embed C2 for test.org/bar
        req = Request('http://test.org/bar')
        self.mw.process_request(req)
        self.assertEquals(req.headers.get('Cookie'), 'C2=value2')

        # embed nothing for test.org/baz
        req = Request('http://test.org/baz')
        self.mw.process_request(req)
        self.assertNotIn('Cookie', req.headers)

    def test_merge_request_cookies(self):
        req = Request('http://test.org/', cookies={'galleta': 'salada'})
        self.assertIs(self.mw.process_request(req), req)
        self.assertEquals(req.headers.get('Cookie'), 'galleta=salada')

        headers = {'Set-Cookie': 'C1=value1; path=/'}
        res = Response('http://test.org/', request=req, headers=headers)
        self.assertIs(self.mw.process_response(res), res)

        req2 = Request('http://test.org/sub1/')
        self.assertIs(self.mw.process_request(req2), req2)
        self.assertEquals(req2.headers.get('Cookie'), 'C1=value1; galleta=salada')

    def test_cookiejar_key(self):
        req = Request('http://test.org/', cookies={'galleta': 'salada'}, meta={'cookiejar': 'store1'})
        self.assertIs(self.mw.process_request(req), req)
        self.assertEquals(req.headers.get('Cookie'), 'galleta=salada')

        headers = {'Set-Cookie': 'C1=value1; path=/'}
        res = Response('http://test.org/', headers=headers, request=req)
        self.assertIs(self.mw.process_response(res), res)

        req2 = Request('http://test.org/', meta=res.meta)
        self.assertIs(self.mw.process_request(req2), req2)
        self.assertEquals(req2.headers.get('Cookie'), 'C1=value1; galleta=salada')


        req3 = Request('http://test.org/', cookies={'galleta': 'dulce'}, meta={'cookiejar': 'store2'})
        self.assertIs(self.mw.process_request(req3), req3)
        self.assertEquals(req3.headers.get('Cookie'), 'galleta=dulce')

        headers = {'Set-Cookie': 'C2=value2; path=/'}
        res2 = Response('http://test.org/', headers=headers, request=req3)
        self.assertIs(self.mw.process_response(res2), res2)

        req4 = Request('http://test.org/', meta=res2.meta)
        self.assertIs(self.mw.process_request(req4), req4)
        self.assertEquals(req4.headers.get('Cookie'), 'C2=value2; galleta=dulce')

        #cookies from hosts with port
        req5_1 = Request('http://test.org:1104/')
        self.assertIs(self.mw.process_request(req5_1), req5_1)

        headers = {'Set-Cookie': 'C1=value1; path=/'}
        res5_1 = Response('http://test.org:1104/', headers=headers, request=req5_1)
        self.assertIs(self.mw.process_response(res5_1), res5_1)

        req5_2 = Request('http://test.org:1104/some-redirected-path')
        self.assertIs(self.mw.process_request(req5_2), req5_2)
        self.assertEquals(req5_2.headers.get('Cookie'), 'C1=value1')

        req5_3 = Request('http://test.org/some-redirected-path')
        self.assertIs(self.mw.process_request(req5_3), req5_3)
        self.assertEquals(req5_3.headers.get('Cookie'), 'C1=value1')

        #skip cookie retrieval for not http request
        req6 = Request('file:///crawlmi/sometempfile')
        self.assertIs(self.mw.process_request(req6), req6)
        self.assertEquals(req6.headers.get('Cookie'), None)
