from twisted.trial import unittest

from .test_selector import XpathSelectorTest
from crawlmi.parser.selectors.lxml_selector import (XPathSelector,
    XmlXPathSelector, HtmlXPathSelector)


class LxmlXpathSelectorTest(unittest.TestCase, XpathSelectorTest):
    xs_cls = XPathSelector
    hxs_cls = HtmlXPathSelector
    xxs_cls = XmlXPathSelector

    def test_nested_select_on_text_nodes(self):
        # FIXME: does not work with lxml backend [upstream]
        r = self.hxs_cls(text=u'<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>')
        x1 = r.select('//div/descendant::text()')
        x2 = x1.select('./preceding-sibling::b[contains(text(), "Options")]')
        self.assertEquals(x2.extract(), [u'<b>Options:</b>'])
    test_nested_select_on_text_nodes.skip = True
