from twisted.trial import unittest

from crawlmi.utils.url import (is_url, is_url_from_any_domain, any_to_uri,
                               requote_url,
                               has_url_any_extension, canonicalize_url)


class UrlTest(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(is_url('http://github.com'))
        self.assertTrue(is_url('https://github.com/'))
        self.assertTrue(is_url('file://localhost/etc/fstab'))

        self.assertFalse(is_url('github.com'))
        self.assertFalse(is_url('/etc/conf'))

    def test_requote_url(self):
        url = 'http://%68%65%2f%6c%6c%6f.com/%'
        self.assertEqual(requote_url(url), 'http://he%2Fllo.com/%')
        # test some real-life urls
        url = 'mailto:development@alleytheatre.org?Subject=Registration%Help'
        self.assertEqual(requote_url(url), 'mailto:development@alleytheatre.org?Subject=Registration%Help')
        url = 'https://maps.google.nl/maps?q=Eekholt+4,+Diemen&%u205Ehl=nl'
        self.assertEqual(requote_url(url), 'https://maps.google.nl/maps?q=Eekholt+4,+Diemen&%u205Ehl=nl')

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

    def test_has_url_any_extension(self):
        url = 'http://www.feedreader.com/releases/FeedReader314Setup.exe'
        self.assertTrue(has_url_any_extension(url, ['.exe', '.pdf']))
        self.assertFalse(has_url_any_extension(url, ['.pdf']))

        url = 'http://servis.idnes.cz/GetFile.aspx?type=idneskindle'
        self.assertTrue(has_url_any_extension(url, ['.aspx']))
        self.assertFalse(has_url_any_extension(url, []))

        url = 'http://www.feedreader.com/blog'
        self.assertFalse(has_url_any_extension(url, ['.com']))

        url = 'http://www.feedreader.com/testimonials.php'
        self.assertTrue(has_url_any_extension(url, ['.php']))
        self.assertFalse(has_url_any_extension(url, ['php']))

    def test_any_to_uri(self):
        self.assertEqual(any_to_uri(r'C:\a\b\c'), 'file:///C:/a/b/c')
        self.assertEqual(any_to_uri('www.google.com'), 'http://www.google.com')
        self.assertEqual(any_to_uri('http://www.google.com'), 'http://www.google.com')

    def test_canonicalize_url(self):
        # simplest case
        self.assertEqual(canonicalize_url('http://www.example.com/'),
                                          'http://www.example.com/')

        # always return a str
        assert isinstance(canonicalize_url(u'http://www.example.com'), str)

        # append missing path
        self.assertEqual(canonicalize_url('http://www.example.com'),
                                          'http://www.example.com/')
        # typical usage
        self.assertEqual(canonicalize_url('http://www.example.com/do?a=1&b=2&c=3'),
                                          'http://www.example.com/do?a=1&b=2&c=3')
        self.assertEqual(canonicalize_url('http://www.example.com/do?c=1&b=2&a=3'),
                                          'http://www.example.com/do?a=3&b=2&c=1')
        self.assertEqual(canonicalize_url('http://www.example.com/do?&a=1'),
                                          'http://www.example.com/do?a=1')

        # sorting by argument values
        self.assertEqual(canonicalize_url('http://www.example.com/do?c=3&b=5&b=2&a=50'),
                                          'http://www.example.com/do?a=50&b=2&b=5&c=3')

        # using keep_blank_values
        self.assertEqual(canonicalize_url('http://www.example.com/do?b=&a=2', keep_blank_values=False),
                                          'http://www.example.com/do?a=2')
        self.assertEqual(canonicalize_url('http://www.example.com/do?b=&a=2'),
                                          'http://www.example.com/do?a=2&b=')
        self.assertEqual(canonicalize_url('http://www.example.com/do?b=&c&a=2', keep_blank_values=False),
                                          'http://www.example.com/do?a=2')
        self.assertEqual(canonicalize_url('http://www.example.com/do?b=&c&a=2'),
                                          'http://www.example.com/do?a=2&b=&c=')

        self.assertEqual(canonicalize_url(u'http://www.example.com/do?1750,4'),
                                           'http://www.example.com/do?1750%2C4=')

        # spaces
        self.assertEqual(canonicalize_url('http://www.example.com/do?q=a space&a=1'),
                                          'http://www.example.com/do?a=1&q=a+space')
        self.assertEqual(canonicalize_url('http://www.example.com/do?q=a+space&a=1'),
                                          'http://www.example.com/do?a=1&q=a+space')
        self.assertEqual(canonicalize_url('http://www.example.com/do?q=a%20space&a=1'),
                                          'http://www.example.com/do?a=1&q=a+space')

        # normalize percent-encoding case (in paths)
        self.assertEqual(canonicalize_url('http://www.example.com/a%a3do'),
                                          'http://www.example.com/a%A3do'),
        # normalize percent-encoding case (in query arguments)
        self.assertEqual(canonicalize_url('http://www.example.com/do?k=b%a3'),
                                          'http://www.example.com/do?k=b%A3')

        # non-ASCII percent-encoding in paths
        self.assertEqual(canonicalize_url('http://www.example.com/a do?a=1'),
                                          'http://www.example.com/a%20do?a=1'),
        self.assertEqual(canonicalize_url('http://www.example.com/a %20do?a=1'),
                                          'http://www.example.com/a%20%20do?a=1'),
        self.assertEqual(canonicalize_url('http://www.example.com/a do\xc2\xa3.html?a=1'),
                                          'http://www.example.com/a%20do%C2%A3.html?a=1')
        # non-ASCII percent-encoding in query arguments
        self.assertEqual(canonicalize_url(u'http://www.example.com/do?price=\xa3500&a=5&z=3'),
                                          u'http://www.example.com/do?a=5&price=%C2%A3500&z=3')
        self.assertEqual(canonicalize_url('http://www.example.com/do?price=\xc2\xa3500&a=5&z=3'),
                                          'http://www.example.com/do?a=5&price=%C2%A3500&z=3')
        self.assertEqual(canonicalize_url('http://www.example.com/do?price(\xc2\xa3)=500&a=1'),
                                          'http://www.example.com/do?a=1&price%28%C2%A3%29=500')

        # urls containing auth and ports
        self.assertEqual(canonicalize_url(u'http://user:pass@www.example.com:81/do?now=1'),
                                          u'http://user:pass@www.example.com:81/do?now=1')

        # remove fragments
        self.assertEqual(canonicalize_url(u'http://user:pass@www.example.com/do?a=1#frag'),
                                          u'http://user:pass@www.example.com/do?a=1')
        self.assertEqual(canonicalize_url(u'http://user:pass@www.example.com/do?a=1#frag', keep_fragments=True),
                                          u'http://user:pass@www.example.com/do?a=1#frag')

        # dont convert safe characters to percent encoding representation
        self.assertEqual(canonicalize_url(
            'http://www.simplybedrooms.com/White-Bedroom-Furniture/Bedroom-Mirror:-Josephine-Cheval-Mirror.html'),
            'http://www.simplybedrooms.com/White-Bedroom-Furniture/Bedroom-Mirror:-Josephine-Cheval-Mirror.html')

        # urllib.quote uses a mapping cache of encoded characters. when parsing
        # an already percent-encoded url, it will fail if that url was not
        # percent-encoded as utf-8, that's why canonicalize_url must always
        # convert the urls to string. the following test asserts that
        # functionality.
        self.assertEqual(canonicalize_url(u'http://www.example.com/caf%E9-con-leche.htm'),
                                           'http://www.example.com/caf%E9-con-leche.htm')

        # domains are case insensitive
        self.assertEqual(canonicalize_url('http://www.EXAMPLE.com/'),
                                          'http://www.example.com/')

        # quoted slash and question sign
        self.assertEqual(canonicalize_url('http://foo.com/AC%2FDC+rocks%3f/?yeah=1'),
                         'http://foo.com/AC%2FDC+rocks%3F/?yeah=1')
        self.assertEqual(canonicalize_url('http://foo.com/AC%2FDC/'),
                         'http://foo.com/AC%2FDC/')

        # utm tags
        self.assertEqual(canonicalize_url('http://gh.com/test?msg=hello&utm_source=gh&utm_medium=320banner&utm_campaign=bpp'),
            'http://gh.com/test?msg=hello')
        self.assertEqual(canonicalize_url('http://gh.com/test?msg=hello#utm_source=gh&utm_medium=320banner&utm_campaign=bpp', keep_fragments=True),
            'http://gh.com/test?msg=hello')
        # when fragment is not query-like, keep utm
        self.assertEqual(canonicalize_url('http://gh.com/test?msg=hello#a;b;utm_source=gh', keep_fragments=True),
            'http://gh.com/test?msg=hello#a;b;utm_source=gh')
