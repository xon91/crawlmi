from twisted.trial import unittest

from crawlmi.utils.python import (to_unicode, to_str, is_binary, get_func_args,
                                  flatten, unique_list)


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

    def test_get_func_args(self):
        def f1(a, b, c):
            pass

        def f2(a, b=None, c=None):
            pass

        class A(object):
            def __init__(self, a, b, c):
                pass

            def method(self, a, b, c):
                pass

        class Callable(object):

            def __call__(self, a, b, c):
                pass

        a = A(1, 2, 3)
        cal = Callable()

        self.assertEqual(get_func_args(f1), ['a', 'b', 'c'])
        self.assertEqual(get_func_args(f2), ['a', 'b', 'c'])
        self.assertEqual(get_func_args(A), ['a', 'b', 'c'])
        self.assertEqual(get_func_args(a.method), ['a', 'b', 'c'])
        self.assertEqual(get_func_args(cal), ['a', 'b', 'c'])
        self.assertEqual(get_func_args(object), [])

        # TODO: how do we fix this to return the actual argument names?
        self.assertEqual(get_func_args(unicode.split), [])
        self.assertEqual(get_func_args(" ".join), [])

    def test_flatten(self):
        self.assertListEqual(
            flatten([1, 2, [3, 4], (5, 6)]),
            [1, 2, 3, 4, 5, 6])
        self.assertListEqual(
            flatten([[[1, 2, 3], (42, None)], [4, 5], [6], 7, (8, 9, 10)]),
            [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10])

    def test_unique_list(self):
        x = [1, 2, 3, 4, 5, 6, 7]
        self.assertListEqual(unique_list(x), [1, 2, 3, 4, 5, 6, 7])
        self.assertListEqual(
            unique_list(x, lambda x: x / 2),
            [1, 2, 4, 6])
        self.assertListEqual(
            unique_list(x, lambda x: x / 3),
            [1, 3, 6])
