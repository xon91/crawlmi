from contextlib import contextmanager
import email.utils
import shutil
import tempfile
import time

from twisted.trial import unittest
from crawlmi.http import Request, Response, HtmlResponse
from crawlmi.middleware.pipelines.httpcache import HttpCache
from crawlmi.utils.test import get_engine


class BaseTest(unittest.TestCase):

    storage_class = 'crawlmi.middleware.pipelines.httpcache.storage.DbmCacheStorage'
    policy_class = 'crawlmi.middleware.pipelines.httpcache.policy.RFC2616Policy'

    def setUp(self):
        self.yesterday = email.utils.formatdate(time.time() - 86400)
        self.today = email.utils.formatdate()
        self.tomorrow = email.utils.formatdate(time.time() + 86400)
        self.tmpdir = tempfile.mkdtemp()
        self.request = Request('http://www.example.com',
                               headers={'User-Agent': 'test'})
        self.response = Response('http://www.example.com',
                                 headers={'Content-Type': 'text/html'},
                                 body='test body',
                                 status=202,
                                 request=self.request)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _get_settings(self, **new_settings):
        settings = {
            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_DIR': self.tmpdir,
            'HTTPCACHE_EXPIRATION_SECS': 1,
            'HTTPCACHE_IGNORE_NON_200_STATUS': False,
            'HTTPCACHE_POLICY': self.policy_class,
            'HTTPCACHE_STORAGE': self.storage_class,
        }
        settings.update(new_settings)
        return settings

    def _get_engine(self, **new_settings):
        return get_engine(self._get_settings(**new_settings))

    @contextmanager
    def _storage(self, **new_settings):
        with self._middleware(**new_settings) as mw:
            yield mw.storage

    @contextmanager
    def _policy(self, **new_settings):
        with self._middleware(**new_settings) as mw:
            yield mw.policy

    @contextmanager
    def _middleware(self, **new_settings):
        engine = self._get_engine(**new_settings)
        mw = HttpCache(engine)
        mw.engine_started()
        try:
            yield mw
        finally:
            mw.engine_stopping()

    def assertEqualResponse(self, response1, response2):
        self.assertEqual(response1.url, response2.url)
        self.assertEqual(response1.status, response2.status)
        self.assertEqual(response1.headers, response2.headers)
        self.assertEqual(response1.body, response2.body)

    def assertEqualRequest(self, request1, request2):
        self.assertEqual(request1.url, request2.url)
        self.assertEqual(request1.headers, request2.headers)
        self.assertEqual(request1.body, request2.body)

    def assertEqualRequestButWithCacheValidators(self, request1, request2):
        self.assertEqual(request1.url, request2.url)
        self.assertNotIn('If-None-Match', request1.headers)
        self.assertNotIn('If-Modified-Since', request1.headers)
        self.assertTrue(any(h in request2.headers for h in ('If-None-Match', 'If-Modified-Since')))
        self.assertEqual(request1.body, request2.body)


class DbmStorageTest(BaseTest):
    def test_storage(self):
        with self._storage() as storage:
            request2 = self.request.copy()
            self.assertIsNone(storage.retrieve_response(request2))

            storage.store_response(self.request, self.response)
            response2 = storage.retrieve_response(request2)
            self.assertIsInstance(response2, HtmlResponse)  # content-type header
            self.assertEqualResponse(self.response, response2)

            time.sleep(2)  # wait for cache to expire
            self.assertIsNone(storage.retrieve_response(request2))

    def test_storage_never_expire(self):
        with self._storage(HTTPCACHE_EXPIRATION_SECS=0) as storage:
            self.assertIsNone(storage.retrieve_response(self.request))
            storage.store_response(self.request, self.response)
            time.sleep(0.5)  # give the chance to expire
            self.assertTrue(storage.retrieve_response(self.request))


class DbmStorageWithCustomDbmModuleTest(DbmStorageTest):
    db_module = 'crawlmi.tests.mocks.dummy_dbm'

    def _get_settings(self, **new_settings):
        new_settings.setdefault('HTTPCACHE_DBM_MODULE', self.db_module)
        return super(DbmStorageWithCustomDbmModuleTest, self)._get_settings(**new_settings)

    def test_custom_dbm_module_loaded(self):
        # make sure our dbm module has been loaded
        with self._storage() as storage:
            self.assertEqual(storage.db_module.__name__, self.db_module)


class DummyPolicyTest(BaseTest):
    policy_class = 'crawlmi.middleware.pipelines.httpcache.policy.DummyPolicy'

    def test_middleware(self):
        with self._middleware() as mw:
            self.assertIs(mw.process_request(self.request), self.request)
            mw.process_response(self.response)
            response = mw.process_request(self.request)
            self.assertIsInstance(response, HtmlResponse)
            self.assertEqualResponse(self.response, response)
            self.assertIn('cached', response.flags)

    def test_different_request_response_urls(self):
        with self._middleware() as mw:
            req = Request('http://host.com/path')
            res = Response('http://host2.net/test.html', request=req)
            self.assertIs(mw.process_request(req), req)
            mw.process_response(res)
            cached = mw.process_request(req)
            self.assertIsInstance(cached, Response)
            self.assertEqualResponse(res, cached)
            self.assertIn('cached', cached.flags)

    def test_middleware_ignore_missing(self):
        with self._middleware(HTTPCACHE_IGNORE_MISSING=True) as mw:
            self.assertIsNone(mw.process_request(self.request))
            mw.process_response(self.response)
            response = mw.process_request(self.request)
            self.assertIsInstance(response, HtmlResponse)
            self.assertEqualResponse(self.response, response)
            self.assertIn('cached', response.flags)

    def test_middleware_ignore_schemes(self):
        # http responses are cached by default
        req = Request('http://test.com/')
        res = Response('http://test.com/', request=req)
        with self._middleware() as mw:
            self.assertIs(mw.process_request(req), req)
            mw.process_response(res)

            cached = mw.process_request(req)
            self.assertIsInstance(cached, Response, type(cached))
            self.assertEqualResponse(res, cached)
            self.assertIn('cached', cached.flags)

        # file response is not cached by default
        req = Request('file:///tmp/t.txt')
        res = Response('file:///tmp/t.txt', request=req)
        with self._middleware() as mw:
            self.assertIs(mw.process_request(req), req)
            mw.process_response(res)

            self.assertIsNone(mw.storage.retrieve_response(req))
            self.assertIs(mw.process_request(req), req)

        # s3 scheme response is cached by default
        req = Request('s3://bucket/key')
        res = Response('http://bucket/key', request=req)
        with self._middleware() as mw:
            self.assertIs(mw.process_request(req), req)
            mw.process_response(res)

            cached = mw.process_request(req)
            self.assertIsInstance(cached, Response, type(cached))
            self.assertEqualResponse(res, cached)
            self.assertIn('cached', cached.flags)

        # ignore s3 scheme
        req = Request('s3://bucket/key2')
        res = Response('http://bucket/key2', request=req)
        with self._middleware(HTTPCACHE_IGNORE_SCHEMES=['s3']) as mw:
            self.assertIs(mw.process_request(req), req)
            mw.process_response(res)

            self.assertIsNone(mw.storage.retrieve_response(req))
            self.assertIs(mw.process_request(req), req)

    def test_middleware_ignore_http_codes(self):
        # test response is not cached
        with self._middleware(HTTPCACHE_IGNORE_STATUS=lambda x: x == 202) as mw:
            self.assertIs(mw.process_request(self.request), self.request)
            mw.process_response(self.response)
            self.assertIsNone(mw.storage.retrieve_response(self.request))
            self.assertIs(mw.process_request(self.request), self.request)

        # test response is cached
        with self._middleware(HTTPCACHE_IGNORE_STATUS=lambda x: x == 203) as mw:
            mw.process_response(self.response)
            response = mw.process_request(self.request)
            self.assertIsInstance(response, HtmlResponse)
            self.assertEqualResponse(self.response, response)
            self.assertIn('cached', response.flags)


class RFC2616PolicyTest(BaseTest):
    policy_class = 'crawlmi.middleware.pipelines.httpcache.policy.RFC2616Policy'

    def _process_requestresponse(self, mw, request, response):
        try:
            result = mw.process_request(request)
            if isinstance(result, Request):
                response.request = result
                result = mw.process_response(response)
            return result
        except Exception:
            print 'Request', request
            print 'Response', response
            print 'Result', result
            raise

    def test_request_cacheability(self):
        res0 = Response(self.request.url, status=200,
                        headers={'Expires': self.tomorrow})
        req0 = Request('http://example.com')
        req1 = req0.replace(headers={'Cache-Control': 'no-store'})
        req2 = req0.replace(headers={'Cache-Control': 'no-cache'})
        with self._middleware() as mw:
            # response for a request with no-store must not be cached
            res1 = self._process_requestresponse(mw, req1, res0)
            self.assertEqualResponse(res1, res0)
            self.assertIsNone(mw.storage.retrieve_response(req1))
            # Re-do request without no-store and expect it to be cached
            res2 = self._process_requestresponse(mw, req0, res0)
            self.assertNotIn('cached', res2.flags)
            res3 = mw.process_request(req0)
            self.assertIn('cached', res3.flags)
            self.assertEqualResponse(res2, res3)
            # request with no-cache directive must not return cached response
            # but it allows new response to be stored
            res0b = res0.replace(body='foo')
            res4 = self._process_requestresponse(mw, req2, res0b)
            self.assertEqualResponse(res4, res0b)
            self.assertNotIn('cached', res4.flags)
            res5 = self._process_requestresponse(mw, req0, None)
            self.assertEqualResponse(res5, res0b)
            self.assertIn('cached', res5.flags)

    def test_response_cacheability(self):
        responses = [
            # 304 is not cacheable no matter what servers sends
            (False, 304, {}),
            (False, 304, {'Last-Modified': self.yesterday}),
            (False, 304, {'Expires': self.tomorrow}),
            (False, 304, {'Etag': 'bar'}),
            (False, 304, {'Cache-Control': 'max-age=3600'}),
            # Always obey no-store cache control
            (False, 200, {'Cache-Control': 'no-store'}),
            (False, 200, {'Cache-Control': 'no-store, max-age=300'}),  # invalid
            (False, 200, {'Cache-Control': 'no-store', 'Expires': self.tomorrow}),  # invalid
            # Ignore responses missing expiration and/or validation headers
            (False, 200, {}),
            (False, 302, {}),
            (False, 307, {}),
            (False, 404, {}),
            # Cache responses with expiration and/or validation headers
            (True, 200, {'Last-Modified': self.yesterday}),
            (True, 203, {'Last-Modified': self.yesterday}),
            (True, 300, {'Last-Modified': self.yesterday}),
            (True, 301, {'Last-Modified': self.yesterday}),
            (True, 401, {'Last-Modified': self.yesterday}),
            (True, 404, {'Cache-Control': 'public, max-age=600'}),
            (True, 302, {'Expires': self.tomorrow}),
            (True, 200, {'Etag': 'foo'}),
        ]
        with self._middleware() as mw:
            for idx, (shouldcache, status, headers) in enumerate(responses):
                req0 = Request('http://example-%d.com' % idx)
                res0 = Response(req0.url, status=status, headers=headers)
                res1 = self._process_requestresponse(mw, req0, res0)
                res304 = res0.replace(status=304)
                res2 = self._process_requestresponse(mw, req0, res304 if shouldcache else res0)
                self.assertEqualResponse(res1, res0)
                self.assertEqualResponse(res2, res0)
                resc = mw.storage.retrieve_response(req0)
                if shouldcache:
                    self.assertEqualResponse(resc, res1)
                    self.assertTrue('cached' in res2.flags and res2.status != 304)
                else:
                    self.assertFalse(resc)
                    self.assertNotIn('cached', res2.flags)

    def test_cached_and_fresh(self):
        sample_data = [
            (200, {'Date': self.yesterday, 'Expires': self.tomorrow}),
            (200, {'Date': self.yesterday, 'Cache-Control': 'max-age=86405'}),
            (200, {'Age': '299', 'Cache-Control': 'max-age=300'}),
            # Obey max-age if present over any others
            (200, {'Date': self.today,
                   'Age': '86405',
                   'Cache-Control': 'max-age=' + str(86400 * 3),
                   'Expires': self.yesterday,
                   'Last-Modified': self.yesterday,
                   }),
            # obey Expires if max-age is not present
            (200, {'Date': self.yesterday,
                   'Age': '86400',
                   'Cache-Control': 'public',
                   'Expires': self.tomorrow,
                   'Last-Modified': self.yesterday,
                   }),
            # Default missing Date header to right now
            (200, {'Expires': self.tomorrow}),
            # Firefox - Expires if age is greater than 10% of (Date - Last-Modified)
            (200, {'Date': self.today, 'Last-Modified': self.yesterday, 'Age': str(86400 / 10 - 1)}),
            # Firefox - Set one year maxage to permanent redirects missing expiration info
            (300, {}), (301, {}), (308, {}),
        ]
        with self._middleware() as mw:
            for idx, (status, headers) in enumerate(sample_data):
                req0 = Request('http://example-%d.com' % idx)
                res0 = Response(req0.url, status=status, headers=headers)
                # cache fresh response
                res1 = self._process_requestresponse(mw, req0, res0)
                self.assertEqualResponse(res1, res0)
                self.assertNotIn('cached', res1.flags)
                # return fresh cached response without network interaction
                res2 = self._process_requestresponse(mw, req0, None)
                self.assertEqualResponse(res1, res2)
                self.assertIn('cached', res2.flags)

    def test_cached_and_stale(self):
        sample_data = [
            (200, {'Date': self.today, 'Expires': self.yesterday}),
            (200, {'Date': self.today, 'Expires': self.yesterday, 'Last-Modified': self.yesterday}),
            (200, {'Expires': self.yesterday}),
            (200, {'Expires': self.yesterday, 'ETag': 'foo'}),
            (200, {'Expires': self.yesterday, 'Last-Modified': self.yesterday}),
            (200, {'Expires': self.tomorrow, 'Age': '86405'}),
            (200, {'Cache-Control': 'max-age=86400', 'Age': '86405'}),
            # no-cache forces expiration, also revalidation if validators exists
            (200, {'Cache-Control': 'no-cache'}),
            (200, {'Cache-Control': 'no-cache', 'ETag': 'foo'}),
            (200, {'Cache-Control': 'no-cache', 'Last-Modified': self.yesterday}),
        ]
        with self._middleware() as mw:
            for idx, (status, headers) in enumerate(sample_data):
                req0 = Request('http://example-%d.com' % idx)
                res0a = Response(req0.url, status=status, headers=headers)
                # cache expired response
                res1 = self._process_requestresponse(mw, req0, res0a)
                self.assertEqualResponse(res1, res0a)
                self.assertNotIn('cached', res1.flags)
                # Same request but as cached response is stale a new response must
                # be returned
                res0b = res0a.replace(body='bar')
                res2 = self._process_requestresponse(mw, req0, res0b)
                self.assertEqualResponse(res2, res0b)
                self.assertNotIn('cached', res2.flags)
                # Previous response expired too, subsequent request to same
                # resource must revalidate and succeed on 304 if validators
                # are present
                if 'ETag' in headers or 'Last-Modified' in headers:
                    res0c = res0b.replace(status=304)
                    res3 = self._process_requestresponse(mw, req0, res0c)
                    self.assertEqualResponse(res3, res0b)
                    self.assertIn('cached', res3.flags)
