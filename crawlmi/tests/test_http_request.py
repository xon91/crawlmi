import unittest2

from crawlmi.http.headers import Headers
from crawlmi.http.request import Request


gh_url = 'http://www.github.com/'


class RequestTest(unittest2.TestCase):

    def test_init(self):
        self.assertRaises(Exception, Request)
        self.assertIsInstance(Request(url=gh_url), Request)
        self.assertRaises(Exception, Request, url=gh_url, hello='world')

        def test_copy_dict(original, copied, name):
            self.assertIsInstance(copied, dict, name)
            self.assertDictEqual(original, copied, name)
            self.assertIsNot(original, copied, name)

        r = Request(url=gh_url)
        self.assertIsInstance(r.headers, Headers)
        self.assertIsInstance(r.meta, dict)
        self.assertIsInstance(r.history, list)

        # test copiing of parameters
        headers = Headers({'Accept': 'gzip', 'Custom-Header': 'nothing to tell you'})
        meta = {'a': 'b', 'c': 'd'}
        params = {'a': 10, 'b': 20}
        history = ['a', 'b']
        encoding = 'latin1'
        body = u'Price: \xa3100'
        r = Request(url=gh_url, method='post', headers=headers, body=body,
            encoding=encoding, meta=meta, params=params, history=history)
        self.assertEqual(r.url, 'http://www.github.com/?a=10&b=20')
        self.assertEqual(r.method, 'POST')
        self.assertEqual(r.encoding, 'latin1')
        self.assertEqual(r.body, 'Price: \xa3100')

        test_copy_dict(headers, r.headers, 'headers')
        test_copy_dict(meta, r.meta, 'meta')
        self.assertIsInstance(r.history, list)
        self.assertListEqual(r.history, history)
        self.assertIsNot(r.history, history)

    def test_properties(self):
        r = Request(url=gh_url, body='Hello', encoding='utf-8')

        def set_url():
            r.url = 'http://github.com/'
        self.assertEqual(r.url, gh_url)
        self.assertRaises(AttributeError, set_url)

        def set_method():
            r.method = 'POST'
        self.assertEqual(r.method, 'GET')
        self.assertRaises(AttributeError, set_method)

        def set_body():
            r.body = 'world'
        self.assertEqual(r.body, 'Hello')
        self.assertRaises(AttributeError, set_body)

        def set_encoding():
            r.encoding = 'utf-8'
        self.assertEqual(r.encoding, 'utf-8')
        self.assertRaises(AttributeError, set_encoding)

    def test_eq(self):
        r1 = Request(url='http://www.github.com/')
        r2 = Request(url='http://www.github.com/')
        self.assertNotEqual(r1, r2)

        s = set()
        s.add(r1)
        s.add(r2)
        self.assertEqual(len(s), 2)

    def test_original_url(self):
        r = Request(url=gh_url)
        self.assertEqual(r.original_url, gh_url)
        r.history.append('x')
        self.assertEqual(r.original_url, 'x')
        r.history.append('y')
        self.assertEqual(r.original_url, 'x')

    def test_prepare_method(self):
        r = Request(url=gh_url)
        self.assertEqual(r.method, 'GET')
        self.assertEqual(r._prepare_method('gEt'), 'GET')
        self.assertEqual(r._prepare_method('post'), 'POST')
        self.assertEqual(r._prepare_method('f.adsf/dsaf,'), 'F.ADSF/DSAF,')
        self.assertIsInstance(r._prepare_method(u'get'), str)

    def test_headers(self):
        r = Request(url=gh_url)
        self.assertIsInstance(r.headers, Headers)
        self.assertDictEqual(r.headers, {})
        r = Request(url=gh_url, headers={'content': 'html'})
        self.assertDictEqual(r.headers, {'Content': ['html']})

        # apply the correct encoding
        headers = {'a': u'mi\xa3no'}
        r = Request(url=gh_url, headers=headers)
        self.assertDictEqual(r.headers, {'A': ['mi\xc2\xa3no']})
        r_latin1 = Request(url=gh_url, encoding='latin1', headers=headers)
        self.assertDictEqual(r_latin1.headers, {'A': ['mi\xa3no']})

    def test_prepare_body(self):
        r = Request(url=gh_url)
        r_latin1 = Request(url=gh_url, encoding='latin1')

        self.assertEqual(r._prepare_body(''), '')

        body = r._prepare_body(u'Price: \xa3100')
        self.assertIsInstance(body, str)
        self.assertEqual(body, 'Price: \xc2\xa3100')
        latin_body = r_latin1._prepare_body(u'Price: \xa3100')
        self.assertEqual(latin_body, 'Price: \xa3100')
        self.assertEqual(r._prepare_body(10), '10')

    def test_encode_params(self):
        r = Request(url=gh_url)
        r_latin1 = Request(url=gh_url, encoding='latin1')

        # test interface
        self.assertEqual(r._encode_params('mimino'), 'mimino')
        self.assertEqual(r._encode_params(u'mi\xa3no'), 'mi\xc2\xa3no')
        self.assertEqual(r_latin1._encode_params(u'mi\xa3no'), 'mi\xa3no')
        self.assertEqual(r._encode_params({'hello': 'world'}), 'hello=world')
        self.assertIn(r._encode_params({'a': 'b', 'c': 'd'}), ['a=b&c=d', 'c=d&a=b'])
        self.assertEqual(r._encode_params([('a', 'b'), ('c', 'd')]), 'a=b&c=d')
        self.assertEqual(r._encode_params([('a', ''), ('c', '10')]), 'a=&c=10')

        self.assertRaises(Exception, r._encode_params)
        self.assertRaises(Exception, r._encode_params, 10)
        self.assertRaises(Exception, r._encode_params, ['hello', 'world'])

        # test quoting
        self.assertEqual(r._encode_params(
            [('a', u'mi\xa3no'), ('b', 'mi\xc2\xa3no')]),
            'a=mi%C2%A3no&b=mi%C2%A3no')
        self.assertEqual(r._encode_params(
            {'! #$%&\'()*+,': '/:;=?@[]~'}),
            '%21+%23%24%25%26%27%28%29%2A%2B%2C=%2F%3A%3B%3D%3F%40%5B%5D%7E')

    def test_prepare_url(self):
        def test(r, original, expected):
            prepared = r._prepare_url(original, {})
            self.assertEqual(prepared, expected, original)

        r = Request(url=gh_url)
        r_latin1 = Request(url=gh_url, encoding='latin1')

        test(r, 'http://www.github.org/path', 'http://www.github.org/path')

        # url quoting
        test(r, 'http://www.github.org/blank%20space', 'http://www.github.org/blank%20space')
        test(r, 'http://www.github.org/blank space', 'http://www.github.org/blank%20space')

        # url encoding
        test(r, u'http://www.github.org/price/\xa3', 'http://www.github.org/price/%C2%A3')
        test(r_latin1, u'http://www.github.org/price/\xa3', 'http://www.github.org/price/%A3')

        # empty scheme or netloc
        self.assertRaises(ValueError, r._prepare_url, '', {})
        self.assertRaises(ValueError, r._prepare_url, 'www.github.com', {})
        self.assertRaises(ValueError, r._prepare_url, '/etc/fstab', {})
        self.assertRaises(ValueError, r._prepare_url, 'http://', {})

        # bad url type
        self.assertRaises(TypeError, r._prepare_url, 10, {})

        # empty path
        test(r, 'http://www.github.com', 'http://www.github.com/')

        # url and params and fragments
        r2 = Request(u'http://www.github.com/hello \xa3 world/?a=10,20&b=30#start=10',
                     params={'c': 'linkin \xa3 park'})
        self.assertEqual(r2.url, 'http://www.github.com/hello%20%C2%A3%20world/?a=10,20&b=30&c=linkin+%A3+park#start=10')
        self.assertEqual(r2.scheme, 'http')
        self.assertEqual(r2.netloc, 'www.github.com')
        self.assertEqual(r2.path, '/hello%20%C2%A3%20world/')
        self.assertEqual(r2.params, '')
        self.assertEqual(r2.query, 'a=10,20&b=30&c=linkin+%A3+park')
        self.assertEqual(r2.fragment, 'start=10')

        # ajax excaping
        test(r, 'http://www.example.com/ajax.html#!key1=value1&key2=value2',
            'http://www.example.com/ajax.html?_escaped_fragment_=key1=value1%26key2=value2')
        test(r, u'http://www.example.com/ajax.html#!key=value',
            'http://www.example.com/ajax.html?_escaped_fragment_=key=value')
        test(r, 'http://www.example.com?user=userid#!key1=value1&key2=value2',
            'http://www.example.com/?user=userid&_escaped_fragment_=key1=value1%26key2=value2')

        # file uri
        test(r, 'file://localhost/etc/fstab', 'file://localhost/etc/fstab')
        test(r, 'file:///etc/fstab', 'file:///etc/fstab')
        test(r, 'file://localhost/c|/WINDOWS/clock.avi', 'file://localhost/c%7C/WINDOWS/clock.avi')
        test(r, 'file:///c|/WINDOWS/clock.avi', 'file:///c%7C/WINDOWS/clock.avi')
        test(r, 'file://localhost/c:/WINDOWS/clock.avi', 'file://localhost/c:/WINDOWS/clock.avi')
        test(r, 'file:///c:/WINDOWS/my clock.avi', 'file:///c:/WINDOWS/my%20clock.avi')

    def test_copy(self):
        def somecallback():
            pass

        r1 = Request('http://www.example.com', callback=somecallback,
            errback=somecallback, method='post', headers={'hello': 'world'},
            params={'a': 'b'}, body='blablabla', meta={'c': 'd'}, proxy='123',
            priority=10, history=[1, 2, 3], encoding='latin1')
        r2 = r1.copy()

        self.assertIs(r1.callback, somecallback)
        self.assertIs(r1.errback, somecallback)
        self.assertIs(r2.callback, r1.callback)
        self.assertIs(r2.errback, r2.errback)

        self.assertEqual(r1.url, r2.url)
        self.assertEqual(r1.method, r2.method)
        self.assertIsNot(r1.headers, r2.headers)
        self.assertDictEqual(r1.headers, r2.headers)
        self.assertIsNot(r1.meta, r2.meta)
        self.assertDictEqual(r1.meta, r2.meta)
        self.assertIsNot(r1.history, r2.history)
        self.assertListEqual(r1.history, r2.history)
        self.assertEqual(r1.body, r2.body)
        self.assertEqual(r1.proxy, r2.proxy)
        self.assertEqual(r1.priority, r2.priority)
        self.assertEqual(r1.encoding, r2.encoding)

    def test_copy_inherited_classes(self):
        class CustomRequest(Request):
            pass

        r1 = CustomRequest('http://www.example.com')
        r2 = r1.copy()
        self.assertIsInstance(r2, CustomRequest)

    def test_replace(self):
        r1 = Request('http://www.example.com', method='GET')
        headers = Headers(dict(r1.headers, key='value'))
        r2 = r1.replace(method='POST', body='New body', headers=headers)
        self.assertEqual(r1.url, r2.url)
        self.assertEqual((r1.method, r2.method), ('GET', 'POST'))
        self.assertEqual((r1.body, r2.body), ('', 'New body'))
        self.assertEqual((r1.headers, r2.headers), (Headers(), headers))

        r3 = Request('http://www.example.com', meta={'a': 1})
        r4 = r3.replace(url='http://www.example.com/2', body='', meta={})
        self.assertEqual(r4.url, 'http://www.example.com/2')
        self.assertEqual(r4.body, '')
        self.assertEqual(r4.meta, {})
