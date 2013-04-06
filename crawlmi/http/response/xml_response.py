from crawlmi.http import TextResponse
from crawlmi.parser.selectors import XmlXPathSelector


class XmlResponse(TextResponse):
    def __init__(self, *args, **kwargs):
        super(XmlResponse, self).__init__(*args, **kwargs)
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = XmlXPathSelector(self)
        return self._selector
