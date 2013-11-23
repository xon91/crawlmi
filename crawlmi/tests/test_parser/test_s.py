from collections import defaultdict

from twisted.trial import unittest

from crawlmi.compat import optional_features
from crawlmi.http import HtmlResponse
from crawlmi.parser import SValidationError, S
from crawlmi.parser.selectors import HtmlXPathSelector
from crawlmi.tests import get_testdata


class STest(unittest.TestCase):
    def test_xpath(self):
        body = get_testdata('pages', 'ip_page.html')
        response = HtmlResponse(url='http://myip.com/list', body=body)
        hxs = response.selector

        # test valid parsing
        valid_ts = S('_', '//div[@id="main"]', quant='1', children=[
            S('title', 'h1', quant='1', value='text()'),
            S('full_title_script', 'h1|div[@id="subtitle"]/h2', quant='2', value='descendant-or-self::text()'),
            # although the following statement gives the same elements, it gives them in different order
            # S('full_title_script', '(h1|div[@id="subtitle"]/h2)/descendant-or-self::*', quant='+', value='text()'),
            S('full_title_no_script', 'h1|div[@id="subtitle"]/h2', quant='2', value='descendant-or-self::*[name()!="script"]/text()'),
            S('full_title_script_bad', '(h1|div[@id="subtitle"]/h2)//*', quant='+', value='text()'),

            S('_list', 'ul[@id="ip_list"]', quant='1', children=[
                S('_ips', 'li', quant='6', group='ips', children=[
                    S('ip', 'span[@class="ip"]', quant='1', value='text()'),
                    S('port', 'span[@class="port"]', quant='1', value='text()'),
                    S('ip_port', 'self::*', value='descendant-or-self::text()'),
                ])
            ]),

            S('url', 'descendant-or-self::a', quant='1', value='@href', callback=S.absolute_url),
            S('empty', 'div[@id="empty"]', quant='1', value='text()'),
            S('footer', 'following-sibling::div[@id="footer"]', quant='1', children=[
                S('footer_links', 'a', quant='+', value='@href', callback=S.absolute_url)
            ]),
            S('nonexistent', 'div/div/div', quant='?', value='text()')
        ])

        # validation without context, when context is expected
        self.assertRaises(SValidationError, valid_ts.parse, hxs)

        parsed = valid_ts.parse(response)

        self.assertItemsEqual(parsed, ['title', 'full_title_script', 'full_title_no_script', 'full_title_script_bad', 'ips',
            'url', 'empty', 'footer', 'footer_links'])  # nonexistent is missing!

        # title
        self.assertIsInstance(parsed['title'], list)
        self.assertListEqual(parsed['title'], [u'Here is the list of some ', u' addresses '])  # text inside strong is not pased
        # full_title
        self.assertListEqual(parsed['full_title_script'], [u'Here is the list of some ', u'ip',
            u' addresses ', u'!!!', u'Just ', u'some', u' ', u'this is bad', u' other text.'])  # order of text nodes is perserved
        self.assertListEqual(parsed['full_title_no_script'], [u'Here is the list of some ', u'ip',
            u' addresses ', u'!!!', u'Just ', u'some', u' ', u' other text.'])  # same result as before, excluding script content
        self.assertListEqual(parsed['full_title_script_bad'], [u'ip', u'!!!', u'some', u'this is bad'])  # this only took the inner nodes
        # ips
        self.assertIsInstance(parsed['ips'], list)
        self.assertEqual(len(parsed['ips']), 6)
        first = parsed['ips'][0]
        self.assertIsInstance(first, defaultdict)
        self.assertItemsEqual(first, ['ip', 'port', 'ip_port'])
        self.assertListEqual(first['ip'], [u'123.44.1.9'])
        self.assertIsInstance(first['ip'][0], unicode)  # parsed objects are always unicode
        self.assertListEqual(first['port'], [u'80'])
        self.assertListEqual(first['ip_port'], [u'123.44.1.9', u':', u'80'])
        # url
        self.assertListEqual(parsed['url'], [u'http://myip.com/url1'])
        self.assertIsInstance(parsed['url'][0], unicode)  # even urls are unicode after being processed
        # empty
        self.assertListEqual(parsed['empty'], [])  # even though we matched 1 tag empty, the was no text and the returned list is empty
        # footer
        self.assertIsInstance(parsed['footer'][0], HtmlXPathSelector)
        self.assertListEqual(parsed['footer_links'], [u'http://myip.com/url2', u'http://google.com/'])

    def test_css(self):
        body = get_testdata('pages', 'ip_page.html')
        response = HtmlResponse(url='http://myip.com/list', body=body)
        hxs = response.selector

        valid_ts = S('_', css='div#main', quant='1', children=[
            S('all_ip', css='span.ip', quant='7'),
            S('_', css='ul#ip_list', quant='1', children=[
                S('list_ip', css='span.ip', quant='6')
            ]),
        ])
        parsed = valid_ts.parse(hxs)
        self.assertRaises(TypeError, S, '_')
        self.assertRaises(TypeError, S, '_', 'div[@id="main]', css='div#main')

    test_css.skip = 'cssselect' not in optional_features

    def test_get_nodes(self):
        node1 = S('node', '.')
        node2 = S('node', '.')
        ts = S('_main', '.', children=[
            node1,
            S('_inner', '.', children=[
                node2,
                node1,
            ])
        ])
        self.assertListEqual(ts.get_nodes('_main'), [ts])
        self.assertListEqual(ts.get_nodes('node'), [node1, node2, node1])
        self.assertListEqual(ts.get_nodes('non-existent'), [])
