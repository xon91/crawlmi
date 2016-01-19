import re
from urlparse import urljoin

from crawlmi.http import TextResponse
from crawlmi.parser.selectors import HtmlXPathSelector
from crawlmi.utils.url import requote_url

from xextract.extractors.lxml_extractor import HtmlXPathExtractor


_base_url_re = re.compile(r'<base\s+href\s*=\s*[\"\']\s*([^\"\'\s]+)\s*[\"\']', re.IGNORECASE)


class HtmlResponse(TextResponse):
    def __init__(self, *args, **kwargs):
        super(HtmlResponse, self).__init__(*args, **kwargs)
        self._selector = None
        self._extractor = None
        self._base_url = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = HtmlXPathSelector(self)
        return self._selector

    @property
    def extractor(self):
        if self._extractor is None:
            self._extractor = HtmlXPathExtractor(self.text)
        return self._extractor

    @property
    def base_url(self):
        if self._base_url is None:
            self._base_url = self.url
            chunk = self.body[:4096]
            m = _base_url_re.search(chunk)
            if m:
                self._base_url = urljoin(self._base_url, m.group(1))
            self._base_url = requote_url(self._base_url)
        return self._base_url
