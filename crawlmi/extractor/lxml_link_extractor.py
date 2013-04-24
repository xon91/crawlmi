import lxml.html

from crawlmi import log
from crawlmi.extractor import Link, BaseLinkExtractor
from crawlmi.http import HtmlResponse
from crawlmi.utils.python import to_str, to_unicode
from crawlmi.utils.url import requote_url


class LxmlLinkExtractor(BaseLinkExtractor):
    def _extract_links(self, response):
        # only works for html documents
        if not isinstance(response, HtmlResponse) or not response.body:
            return []

        html = lxml.html.fromstring(response.text)
        html.make_links_absolute(response.url)
        links = []
        for e, a, l, p in html.iterlinks():
            if self.tag_func(e.tag):
                if self.attr_func(a):
                    try:
                        url = requote_url(to_str(l, response.encoding))
                        text = e.text or u''
                        text = to_unicode(text, response.encoding,
                                          errors='replace')
                    except Exception as e:
                        log.msg(
                            format='Error occurred while extracting links from %(url)s. Error (%(etype)s): %(error)s',
                            level=log.WARNING, url=response.url, etype=type(e),
                            error=e)
                    else:
                        links.append(Link(url=url, text=text))
        return links
