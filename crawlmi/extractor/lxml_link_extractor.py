from crawlmi import log
from crawlmi.extractor import Link, BaseLinkExtractor
from crawlmi.http import HtmlResponse
from crawlmi.utils.lxml_fix import get_html
from crawlmi.utils.python import to_str, to_unicode
from crawlmi.utils.url import requote_url


class LxmlLinkExtractor(BaseLinkExtractor):
    def _extract_links(self, response):
        # only works for html documents
        if not isinstance(response, HtmlResponse) or not response.body:
            return []

        html = get_html(response)
        html.make_links_absolute(response.url)
        links = []
        for e, a, l, p in html.iterlinks():
            if self.tag_func(e.tag):
                if self.attr_func(a):
                    try:
                        url = requote_url(to_str(to_unicode(l, 'utf-8'), response.encoding))
                        text = e.text or u''
                        text = to_unicode(text, 'utf-8')
                    except Exception as e:
                        log.msg(
                            format='Error occurred while extracting links from %(url)s. Error (%(etype)s): %(error)s',
                            level=log.WARNING, url=response.url, etype=type(e),
                            error=e)
                    else:
                        links.append(Link(url=url, text=text))
        return links
