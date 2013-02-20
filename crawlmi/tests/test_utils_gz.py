from os.path import join

from twisted.trial import unittest

from crawlmi.tests import tests_datadir
from crawlmi.utils.gz import gunzip


SAMPLE_DIR = join(tests_datadir, 'compressed')

class GzTest(unittest.TestCase):
    def test_gunzip_basic(self):
        with open(join(SAMPLE_DIR, 'feed-sample1.xml.gz'), 'rb') as f:
            text = gunzip(f.read())
            self.assertEqual(len(text), 9950)

    def test_gunzip_truncated(self):
        with open(join(SAMPLE_DIR, 'truncated-crc-error.gz'), 'rb') as f:
            text = gunzip(f.read())
            assert text.endswith('</html')

    def test_gunzip_no_gzip_file_raises(self):
        with open(join(SAMPLE_DIR, 'feed-sample1.xml'), 'rb') as f:
            self.assertRaises(IOError, gunzip, f.read())

    def test_gunzip_truncated_short(self):
        with open(join(SAMPLE_DIR, 'truncated-crc-error-short.gz'), 'rb') as f:
            text = gunzip(f.read())
            assert text.endswith('</html>')
