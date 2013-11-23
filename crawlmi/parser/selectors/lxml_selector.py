from lxml import etree

from crawlmi.http import TextResponse
from crawlmi.parser.selectors.selector_list import XPathSelectorList
from crawlmi.utils.python import to_str
from crawlmi.utils.trackref import object_ref


class XPathSelector(object_ref):
    _parser = etree.HTMLParser
    _tostring_method = 'html'

    def __init__(self, response=None, text=None, namespaces=None, _root=None):
        if text is not None:
            response = TextResponse(url='about:blank', body=to_str(text))
        if response is not None:
            _root = self._get_root(response)

        self.namespaces = namespaces
        self.response = response
        self._root = _root

    def _get_root(self, response):
        url = response.url
        body = response.text.strip().encode('utf-8') or '<html/>'
        parser = self._parser(recover=True, encoding='utf-8')
        return etree.fromstring(body, parser=parser, base_url=url)

    def select(self, xpath):
        if not hasattr(self._root, 'xpath'):
            return XPathSelectorList([])

        if isinstance(xpath, etree.XPath):
            result = xpath(self._root)
        else:
            result = self._root.xpath(xpath, namespaces=self.namespaces)

        if not isinstance(result, list):
            result = [result]

        return XPathSelectorList([self.__class__(_root=x, namespaces=self.namespaces)
                                  for x in result])

    def extract(self):
        try:
            return etree.tostring(self._root, method=self._tostring_method,
                                  encoding=unicode, with_tail=False)
        except (AttributeError, TypeError):
            if self._root is True:
                return u'1'
            elif self._root is False:
                return u'0'
            else:
                return unicode(self._root)

    def register_namespace(self, prefix, uri):
        if self.namespaces is None:
            self.namespaces = {}
        self.namespaces[prefix] = uri

    def compile_xpath(self, xpath):
        return etree.XPath(xpath, namespaces=self.namespaces)

    def __nonzero__(self):
        return bool(self.extract())

    def __str__(self):
        data = repr(self.extract()[:40])
        return '<%s data=%s>' % (type(self).__name__, data)

    __repr__ = __str__


class XmlXPathSelector(XPathSelector):
    _parser = etree.XMLParser
    _tostring_method = 'xml'


class HtmlXPathSelector(XPathSelector):
    _parser = etree.HTMLParser
    _tostring_method = 'html'
