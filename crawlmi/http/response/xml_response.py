from crawlmi.http import TextResponse
from crawlmi.parser.selectors import XmlXPathSelector
from xextract.extractors.lxml_extractor import XmlXPathExtractor


class XmlResponse(TextResponse):
    def __init__(self, *args, **kwargs):
        super(XmlResponse, self).__init__(*args, **kwargs)
        self._selector = None
        self._extractor = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = XmlXPathSelector(self)
            self._selector.namespaces = self._selector._root.nsmap
        return self._selector

    @property
    def extractor(self):
        if self._extractor is None:
            self._extractor = XmlXPathExtractor(self.text)
        return self._extractor
