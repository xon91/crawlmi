from twisted.trial import unittest

from crawlmi.utils.python import to_unicode, to_str, is_binary


class UtilsPythonTest(unittest.TestCase):

    def test_to_str(self):
        self.assertEqual(to_str(u'\xa3 49'), '\xc2\xa3 49')
        self.assertEqual(to_str(u'\xa3 49', 'latin-1'), '\xa3 49')
        self.assertEqual(to_str('lel\xf1e'), 'lel\xf1e')
        self.assertEqual(to_str([10, 11]), '[10, 11]')
        self.assertIn('?', to_str(u'a\ufffdb', 'latin-1', errors='replace'))

    def test_to_unicode(self):
        self.assertEqual(to_unicode('lel\xc3\xb1e'), u'lel\xf1e')
        self.assertEqual(to_unicode('lel\xf1e', 'latin-1'), u'lel\xf1e')
        self.assertEqual(to_unicode(u'\xf1e\xf1e\xf1e'), u'\xf1e\xf1e\xf1e')
        self.assertEqual(to_unicode([10, 11]), u'[10, 11]')
        self.assertIn(u'\ufffd', to_unicode('a\xedb', 'utf-8', errors='replace'))

    def test_is_binary(self):
        # basic tests
        self.assertFalse(is_binary("hello"))
        # utf-16 strings contain null bytes
        self.assertFalse(is_binary(u"hello".encode('utf-16')))
        # one with encoding
        self.assertFalse(is_binary("<div>Price \xa3</div>"))
        # finally some real binary bytes
        self.assertTrue(is_binary("\x02\xa3"))
