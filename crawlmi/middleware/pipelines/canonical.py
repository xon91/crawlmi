import re
import urlparse

from crawlmi.http import HtmlResponse


class Canonical(object):
    def __init__(self, engine):
        self.canonical_header_re = re.compile(r'<([^>]+)>\s*;\s+rel\s*=\s*[\"\']canonical[\"\']', re.IGNORECASE)
        self.canonical_tag_re = re.compile(r'<link\s+rel\s*=\s*[\"\']canonical[\"\']\s+href\s*=\s*[\"\']\s*([^\"\'\s]+)\s*[\"\']', re.IGNORECASE)

    def process_response(self, response):
        if 'Link' in response.headers:
            m = self.canonical_header_re.search(response.headers['link'])
            if m:
                response.meta['canonical_url'] = urlparse.urljoin(response.base_url, m.group(1))
        if isinstance(response, HtmlResponse):
            m = self.canonical_tag_re.search(response.body[:4096])
            if m:
                response.meta['canonical_url'] = urlparse.urljoin(response.base_url, m.group(1))
        return response
