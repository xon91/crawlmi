from crawlmi.http.response import TextResponse
from crawlmi.parser.selectors import HtmlXPathSelector


class HtmlResponse(TextResponse):
    def __init__(self, *args, **kwargs):
        super(HtmlResponse, self).__init__(*args, **kwargs)
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = HtmlXPathSelector(self)
        return self._selector
