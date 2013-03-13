from lxml import etree

from crawlmi.http.response import TextResponse
from crawlmi.parser.selectors.selector_list import XPathSelectorList
from crawlmi.utils.python import to_str


class XPathSelector(object):
    _parser = etree.HTMLParser
    _tostring_method = 'html'

    def __init__(self, response=None, text=None, namespaces=None, _root=None,
                 _expr=None):
        if text is not None:
            response = TextResponse(url='about:blank', body=to_str(text))
        if response is not None:
            _root = self._get_root(response)

        self.namespaces = namespaces
        self.response = response
        self._root = _root
        self._expr = _expr

    def _get_root(self, response):
        url = response.url
        body = response.text.strip().encode('utf-8') or '<html/>'
        parser = self._parser(recover=True, encoding='utf-8')
        return etree.fromstring(body, parser=parser, base_url=url)

    def select(self, xpath):
        try:
            xpath_call = self._root.xpath
        except AttributeError:
            return XPathSelectorList([])

        try:
            result = xpath_call(xpath, namespaces=self.namespaces)
        except etree.XPathError:
            raise ValueError('Invalid XPath: %s' % xpath)

        if type(result) is not list:
            result = [result]

        result = [self.__class__(_root=x, _expr=xpath, namespaces=self.namespaces)
                  for x in result]
        return XPathSelectorList(result)

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

    def __nonzero__(self):
        return bool(self.extract())

    def __str__(self):
        data = repr(self.extract()[:40])
        return '<%s xpath=%r data=%s>' % (type(self).__name__, self._expr, data)

    __repr__ = __str__


class XmlXPathSelector(XPathSelector):
    _parser = etree.XMLParser
    _tostring_method = 'xml'


class HtmlXPathSelector(XPathSelector):
    _parser = etree.HTMLParser
    _tostring_method = 'html'
