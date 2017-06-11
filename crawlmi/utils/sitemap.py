import re

from crawlmi.http import XmlResponse
from crawlmi.utils.gz import gunzip, gzip_magic_number


def get_sitemap_body(response):
    '''Return the sitemap body contained in the given response, or None if the
    response is not a sitemap.
    '''
    if isinstance(response, XmlResponse):
        return response.body
    elif gzip_magic_number(response):
        return gunzip(response.body)
    # actual gzipped sitemap files are decompressed above ;
    # if we are here (response body is not gzipped)
    # and have a response for .xml.gz,
    # it usually means that it was already gunzipped
    # by HttpCompression middleware,
    # the HTTP response being sent with "Content-Encoding: gzip"
    # without actually being a .xml.gz file in the first place,
    # merely XML gzip-compressed on the fly,
    # in other word, here, we have plain XML
    elif response.url.endswith('.xml') or response.url.endswith('.xml.gz'):
        return response.body


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
