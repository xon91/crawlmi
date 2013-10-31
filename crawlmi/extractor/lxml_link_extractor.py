from urlparse import urlparse, urlunparse

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
        return self._extract_links_from_html(html, response.encoding)

    def _correct_relative_paths(self, url):
        scheme, netloc, path, params, query, fragment = urlparse(url)

        segments = path.split('/')
        # following code is taken from urlparse.urljoin()
        if segments[-1] == '.':
            segments[-1] = ''
        while '.' in segments:
            segments.remove('.')
        while 1:
            i = 1
            n = len(segments) - 1
            while i < n:
                if (segments[i] == '..'
                    and segments[i-1] not in ('', '..')):
                    del segments[i-1:i+1]
                    break
                i = i+1
            else:
                break
        if segments == ['', '..']:
            segments[-1] = ''
        elif len(segments) >= 2 and segments[-1] == '..':
            segments[-2:] = ['']

        # final cleanup
        segments = [x for x in segments if x != '..']
        return urlunparse((scheme, netloc, '/'.join(segments), params, query, fragment))

    def _extract_links_from_html(self, html, response_encoding):
        links = []
        for e, a, l, p in html.iterlinks():
            if self.tag_func(e.tag):
                if self.attr_func(a):
                    try:
                        url = requote_url(to_str(to_unicode(l, 'utf-8'), response_encoding))
                        url = self._correct_relative_paths(url)
                        text = e.text or u''
                        text = to_unicode(text, 'utf-8')
                        nofollow = (e.attrib.get('rel') == 'nofollow')
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
