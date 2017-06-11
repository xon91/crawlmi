from crawlmi.http import TextResponse
from xextract.extractors.lxml_extractor import XmlXPathExtractor


class XmlResponse(TextResponse):
    def __init__(self, *args, **kwargs):
        super(XmlResponse, self).__init__(*args, **kwargs)
        self._extractor = None

    @property
    def extractor(self):
        if self._extractor is None:
            self._extractor = XmlXPathExtractor(self.text)
        return self._extractor
