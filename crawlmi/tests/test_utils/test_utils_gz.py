from os.path import join

from twisted.trial import unittest

from crawlmi.exceptions import DecompressSizeError
from crawlmi.http import Response, Headers
from crawlmi.tests import tests_datadir
from crawlmi.utils.gz import gunzip, is_gzipped


SAMPLE_DIR = join(tests_datadir, 'compressed')

class GzTest(unittest.TestCase):
    def test_gunzip_basic(self):
        with open(join(SAMPLE_DIR, 'feed-sample1.xml.gz'), 'rb') as f:
            text = gunzip(f.read())
            self.assertEqual(len(text), 9950)

    def test_gunzip_truncated(self):
        with open(join(SAMPLE_DIR, 'truncated-crc-error.gz'), 'rb') as f:
            text = gunzip(f.read())
            self.assertTrue(text.endswith('</html'))

    def test_gunzip_no_gzip_file_raises(self):
        with open(join(SAMPLE_DIR, 'feed-sample1.xml'), 'rb') as f:
            self.assertRaises(IOError, gunzip, f.read())

    def test_gunzip_truncated_short(self):
        with open(join(SAMPLE_DIR, 'truncated-crc-error-short.gz'), 'rb') as f:
            text = gunzip(f.read())
            self.assertTrue(text.endswith('</html>'))

    def test_max_length(self):
        with open(join(SAMPLE_DIR, 'feed-sample1.xml.gz'), 'rb') as f:
            raw = f.read()
            self.assertEqual(len(gunzip(raw, 9950)), 9950)
            self.assertRaises(DecompressSizeError, gunzip, raw, 9949)

    def test_is_x_gzipped_right(self):
        hdrs = Headers({"Content-Type": "application/x-gzip"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertTrue(is_gzipped(r1))

    def test_is_gzipped_right(self):
        hdrs = Headers({"Content-Type": "application/gzip"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertTrue(is_gzipped(r1))

    def test_is_gzipped_not_quite(self):
        hdrs = Headers({"Content-Type": "application/gzippppp"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertFalse(is_gzipped(r1))

    def test_is_gzipped_case_insensitive(self):
        hdrs = Headers({"Content-Type": "Application/X-Gzip"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertTrue(is_gzipped(r1))

        hdrs = Headers({"Content-Type": "application/X-GZIP ; charset=utf-8"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertTrue(is_gzipped(r1))

    def test_is_gzipped_empty(self):
        r1 = Response("http://www.example.com")
        self.assertFalse(is_gzipped(r1))

    def test_is_gzipped_wrong(self):
        hdrs = Headers({"Content-Type": "application/javascript"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertFalse(is_gzipped(r1))

    def test_is_gzipped_with_charset(self):
        hdrs = Headers({"Content-Type": "application/x-gzip;charset=utf-8"})
        r1 = Response("http://www.example.com", headers=hdrs)
        self.assertTrue(is_gzipped(r1))

    def test_gunzip_illegal_eof(self):
        with open(join(SAMPLE_DIR, 'unexpected-eof.gz'), 'rb') as f:
            text = gunzip(f.read()).decode('cp1252')
            with open(join(SAMPLE_DIR, 'unexpected-eof-output.txt'), 'rb') as o:
                expected_text = o.read().decode('utf-8')
                self.assertEqual(len(text), len(expected_text))
                self.assertEqual(text, expected_text)
