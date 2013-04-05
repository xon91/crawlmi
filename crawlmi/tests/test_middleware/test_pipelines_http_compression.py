from cStringIO import StringIO
from gzip import GzipFile
from os.path import join

from twisted.trial import unittest

from crawlmi.http.request import Request
from crawlmi.http.response import Response, HtmlResponse
from crawlmi.middleware.pipelines.http_compression import HttpCompression
from crawlmi.tests import tests_datadir
from crawlmi.utils.encoding import normalize_encoding
from crawlmi.utils.test import get_engine


SAMPLE_DIR = join(tests_datadir, 'compressed')


FORMAT = {
    'gzip': ('html-gzip.bin', 'gzip'),
    'x-gzip': ('html-gzip.bin', 'gzip'),
    'rawdeflate': ('html-rawdeflate.bin', 'deflate'),
    'zlibdeflate': ('html-zlibdeflate.bin', 'deflate'),
}


class HttpCompressionTest(unittest.TestCase):
    def setUp(self):
        self.mw = HttpCompression(get_engine())

    def _getresponse(self, coding):
        if coding not in FORMAT:
            raise ValueError()

        sample_file, content_encoding = FORMAT[coding]
        with open(join(SAMPLE_DIR, sample_file), 'rb') as sample:
            body = sample.read()

        headers = {
            'Server': 'Yaws/1.49 Yet Another Web Server',
            'Date': 'Sun, 08 Mar 2009 00:41:03 GMT',
            'Content-Length': len(body),
            'Content-Type': 'text/html',
            'Content-Encoding': content_encoding,
        }

        response = Response('http://github.com/', body=body, headers=headers)
        response.request = Request('http://github.com/', headers={'Accept-Encoding': 'gzip,deflate'})
        return response

    def test_process_request(self):
        request = Request('http://github.com/')
        self.assertNotIn('Accept-Encoding', request.headers)
        request = self.mw.process_request(request)
        self.assertEqual(request.headers.get('Accept-Encoding'), 'x-gzip,gzip,deflate')

    def test_process_response_gzip(self):
        response = self._getresponse('gzip')
        self.assertEqual(response.headers['Content-Encoding'], 'gzip')
        new_response = self.mw.process_response(response)
        self.assertIsNot(new_response, response)
        self.assertTrue(new_response.body.startswith('<!DOCTYPE'))
        self.assertNotIn('Content-Encoding', new_response.headers)

    def test_process_response_rawdeflate(self):
        response = self._getresponse('rawdeflate')
        self.assertEqual(response.headers['Content-Encoding'], 'deflate')
        new_response = self.mw.process_response(response)
        self.assertIsNot(new_response, response)
        self.assertTrue(new_response.body.startswith('<!DOCTYPE'))
        self.assertNotIn('Content-Encoding', new_response.headers)

    def test_process_response_zlibdelate(self):
        response = self._getresponse('zlibdeflate')
        self.assertEqual(response.headers['Content-Encoding'], 'deflate')
        new_response = self.mw.process_response(response)
        self.assertIsNot(new_response, response)
        self.assertTrue(new_response.body.startswith('<!DOCTYPE'))
        self.assertNotIn('Content-Encoding', new_response.headers)

    def test_process_response_plain(self):
        response = Response('http://crawlmitest.org', body='<!DOCTYPE...')
        self.assertFalse(response.headers.get('Content-Encoding'))
        new_response = self.mw.process_response(response)
        self.assertIs(new_response, response)
        self.assertTrue(new_response.body.startswith('<!DOCTYPE'))

    def test_multipleencodings(self):
        response = self._getresponse('gzip')
        response.headers['Content-Encoding'] = ['uuencode', 'gzip']
        new_response = self.mw.process_response(response)
        self.assertIsNot(new_response, response)
        self.assertEqual(new_response.headers.getlist('Content-Encoding'), ['uuencode'])

    def test_process_response_encoding(self):
        headers = {
            'Content-Type': 'text/html',
            'Content-Encoding': 'gzip',
        }
        f = StringIO()
        plain_body = '<html><head><title>Some page</title>'
        zf = GzipFile(fileobj=f, mode='wb')
        zf.write(plain_body)
        zf.close()
        response = Response('http://github.com/', headers=headers, body=f.getvalue())
        new_response = self.mw.process_response(response)
        self.assertIsInstance(new_response, HtmlResponse)
        self.assertEqual(new_response.body, plain_body)
        self.assertEqual(new_response.encoding, normalize_encoding('cp1252'))
