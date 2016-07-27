import re
import urlparse

from crawlmi.http import HtmlResponse
from crawlmi.utils.url import requote_url


class Canonical(object):
    def __init__(self, engine):
        self.canonical_header_re = re.compile(r'<([^>]+)>\s*;\s+rel\s*=\s*[\"\']canonical[\"\']', re.IGNORECASE)
        self.canonical_tag_re = re.compile(r'<link\s+rel\s*=\s*[\"\']canonical[\"\']\s+href\s*=\s*[\"\']\s*([^\"\'\s]+)\s*[\"\']', re.IGNORECASE)

    def process_response(self, response):
        canonical_url = None
        if 'Link' in response.headers:
            m = self.canonical_header_re.search(response.headers['link'])
            if m:
                canonical_url = m.group(1)
        if isinstance(response, HtmlResponse):
            m = self.canonical_tag_re.search(response.body[:4096])
            if m:
                canonical_url = m.group(1)
        if canonical_url:
            response.meta['canonical_url'] = requote_url(urlparse.urljoin(response.base_url, canonical_url))
        return response
