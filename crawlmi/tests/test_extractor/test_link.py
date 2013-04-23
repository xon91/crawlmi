from twisted.trial import unittest

from crawlmi.extractor import Link


class LinkTest(unittest.TestCase):
    def _assert_same_links(self, link1, link2):
        self.assertEqual(link1, link2)
        self.assertEqual(hash(link1), hash(link2))

    def _assert_different_links(self, link1, link2):
        self.assertNotEqual(link1, link2)
        self.assertNotEqual(hash(link1), hash(link2))

    def test_eq_and_hash(self):
        l1 = Link('http://www.example.com')
        l2 = Link('http://www.example.com/other')
        l3 = Link('http://www.example.com')

        self._assert_same_links(l1, l1)
        self._assert_different_links(l1, l2)
        self._assert_same_links(l1, l3)

        l4 = Link('http://www.example.com', text='test')
        l5 = Link('http://www.example.com', text='test2')
        l6 = Link('http://www.example.com', text='test')

        self._assert_same_links(l4, l4)
        self._assert_different_links(l4, l5)
        self._assert_same_links(l4, l6)

    def test_repr(self):
        l1 = Link('http://www.example.com', text='test')
        l2 = eval(repr(l1))
        self._assert_same_links(l1, l2)
