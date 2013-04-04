from twisted.trial import unittest

from crawlmi.utils.url import is_url_from_any_domain


class UrlTest(unittest.TestCase):
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
