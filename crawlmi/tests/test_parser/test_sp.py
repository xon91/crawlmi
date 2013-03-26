from twisted.trial import unittest

from crawlmi.http.response import HtmlResponse
from crawlmi.parser import S, SP
from crawlmi.parser.selectors import HtmlXPathSelector
from crawlmi.tests import get_testdata


basic_ts = S('_page', '//html', quant='1', children=[
    S('title', 'head/title', quant='1'),
    S('_main', 'body/div[@id="main"]', quant='1', children=[
        S('h', 'h1', quant='1', value='descendant-or-self::text()'),
        S('_ips', 'ul[@id="ip_list"]/li', quant='+', group='ips', children=[
            S('ip', 'descendant::span[@class="ip"]', quant='1', value='text()'),
            S('port', 'descendant::span[@class="port"]', quant='1', value='text()'),
        ]),
        S('ports', 'ul[@id="ip_list"]//descendant::span[@class="port"]', quant='+', value='text()'),
        S('nothing', 'a/a/a/a')
    ]),
])


class SPTest(unittest.TestCase):
    def setUp(self):
        body = get_testdata('pages', 'ip_page.html')
        response = HtmlResponse(url='http://myip.com/list', body=body)
        hxs = response.selector
        self.parsed = basic_ts.parse(hxs)

    def test_bad_validate(self):
        s = S('head', '', group='g', children=[
            S('item', '')
        ])

        sp = SP(head2=SP.one)
        self.assertRaises(ValueError, sp.validate, s)

        sp = SP(head=SP(item=SP.one))
        self.assertRaises(ValueError, sp.validate, s)

        sp = SP(head=SP.one)
        missing = sp.validate(s)
        self.assertDictEqual(missing, {'g': {'item': None}})

    def test_basic_proc(self):
        proc = SP(
            title=SP.id,
            h=SP.space,
            ips=SP(
                ip=SP.one,
                port=SP.one,
            ),
            ports=SP.unique,
            nothing=SP.defaultf(42)
        )
        proc.validate(basic_ts)
        data = proc.parse(self.parsed)

        self.assertIsInstance(data['title'][0], HtmlXPathSelector)
        self.assertEqual(data['h'], u'Here is the list of some ip addresses !!!')
        self.assertListEqual(data['ports'], [u'94', u'91', u'90', u'80', u'92', u'93'])
        ips = data['ips']
        self.assertEqual(len(ips), 6)
        self.assertDictEqual(ips[0], {'ip': u'123.44.1.9', 'port': u'80'})
        self.assertEqual(data['nothing'], 42)
