from twisted.trial import unittest

from crawlmi.utils.url import (is_url, is_url_from_any_domain, any_to_uri,
                               path_to_file_uri)


class UrlTest(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(is_url('http://github.com'))
        self.assertTrue(is_url('https://github.com/'))
        self.assertTrue(is_url('file://localhost/etc/fstab'))

        self.assertFalse(is_url('github.com'))
        self.assertFalse(is_url('/etc/conf'))

    def test_is_url_from_any_domain(self):
        url = 'http://www.wheele-bin-art.co.uk/get/product/123'
        self.assertTrue(is_url_from_any_domain(url, ['wheele-bin-art.co.uk']))
        self.assertFalse(is_url_from_any_domain(url, ['art.co.uk']))

        url = 'http://wheele-bin-art.co.uk/get/product/123'
        self.assertTrue(is_url_from_any_domain(url, ['wheele-bin-art.co.uk']))
        self.assertFalse(is_url_from_any_domain(url, ['art.co.uk']))

        url = 'http://192.169.0.15:8080/mypage.html'
        self.assertTrue(is_url_from_any_domain(url, ['192.169.0.15:8080']))
        self.assertFalse(is_url_from_any_domain(url, ['192.169.0.15']))

        url = 'javascript:%20document.orderform_2581_1190810811.mode.value=%27add%27;%20javascript:%20document.orderform_2581_1190810811.submit%28%29'
        self.assertFalse(is_url_from_any_domain(url, ['testdomain.com']))
        self.assertFalse(is_url_from_any_domain(url+'.testdomain.com', ['testdomain.com']))

    def test_any_to_uri(self):
        self.assertEqual(any_to_uri(r'C:\a\b\c'), 'file:///C:/a/b/c')
        self.assertEqual(any_to_uri('www.google.com'), path_to_file_uri('www.google.com'))
        self.assertEqual(any_to_uri('http://www.google.com'), 'http://www.google.com')
