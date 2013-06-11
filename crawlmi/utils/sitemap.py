import re

from crawlmi.http import XmlResponse
from crawlmi.utils.gz import gunzip, is_gzipped


def get_sitemap_body(response):
    '''Return the sitemap body contained in the given response, or None if the
    response is not a sitemap.
    '''
    if isinstance(response, XmlResponse):
        return response.body
    elif is_gzipped(response):
        return gunzip(response.body)
    elif response.url.endswith('.xml'):
        return response.body
    elif response.url.endswith('.xml.gz'):
        return gunzip(response.body)


def iter_urls_from_robots(robots_text):
    '''Returns an iterator over all sitemap urls contained in the given
    robots.txt.
    '''
    for line in robots_text.splitlines():
        if line.lstrip().startswith('Sitemap:'):
            yield line.split(':', 1)[1].strip()


_root_re = re.compile(r'.*?<\s*(\w+)')

def get_sitemap_type(sitemap_text):
    '''Return the type of the sitemap.
    Either `sitemapindex` or `urlset`.
    '''
    root_name = _root_re.search(sitemap_text)
    if root_name:
        return root_name.group(1)
    return ''


_loc_re = re.compile(r'<loc\s*>(.*?)</loc>', re.IGNORECASE | re.DOTALL)

def iter_urls_from_sitemap(sitemap_text):
    '''Return an iterator over all <loc> urls contained in the given sitemap.
    '''
    for match in _loc_re.finditer(sitemap_text):
        yield match.group(1)
