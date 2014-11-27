from crawlmi import log
from crawlmi.extractor import Link, BaseLinkExtractor
from crawlmi.http import HtmlResponse
from crawlmi.utils.lxml_fix import get_html
from crawlmi.utils.python import to_str, to_unicode
from crawlmi.utils.url import requote_url, correct_relative_path


class LxmlLinkExtractor(BaseLinkExtractor):
    def _extract_links(self, response):
        # only works for html documents
        if not isinstance(response, HtmlResponse) or not response.body:
            return []

        html = get_html(response)
        html.make_links_absolute(response.url)
        return self._extract_links_from_html(html, response.encoding)

    def _extract_links_from_html(self, html, response_encoding):
        links = []
        for el, attr, attr_val, pos in html.iterlinks():
            if self.tag_func(el.tag):
                if self.attr_func(attr):
                    try:
                        url = attr_val
                        if isinstance(url, unicode):
                            try:
                                url = to_str(url, response_encoding)
                            except UnicodeEncodeError:
                                # fallback
                                url = to_str(url, 'utf-8')
                        url = requote_url(url)
                        url = correct_relative_path(url)
                        text = el.text or u''
                        text = to_unicode(text, 'utf-8')
                        nofollow = (el.attrib.get('rel') == 'nofollow')
                    except Exception as e:
                        log.msg(
                            format='Error occurred while extracting links from %(url)s. Error (%(etype)s): %(error)s',
                            level=log.WARNING, url=html.base_url, etype=type(e),
                            error=e)
                    else:
                        links.append(Link(url=url, text=text, nofollow=nofollow))
        return links

    def extract_links_from_html(self, html, response_encoding, process_links=None):
        links = self._extract_links_from_html(html, response_encoding)
        return self._process_links(links, process_links)
