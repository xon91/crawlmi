import os
import re
import urllib
from urlparse import urlparse, urlunparse, parse_qsl

from crawlmi.utils.python import to_str


# The unreserved URL characters (RFC 3986)
UNRESERVED_SET = frozenset(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    '0123456789-._~')


def _unquote_unreserved(url):
    '''Un-escape any percent-escape sequences in a URL that are unreserved
    characters. This leaves all reserved, illegal and non-ASCII bytes encoded.
    '''
    parts = url.split('%')
    for i in range(1, len(parts)):
        h = parts[i][0:2]
        if len(h) == 2 and h.isalnum():
            c = chr(int(h, 16))
            if c in UNRESERVED_SET:
                parts[i] = c + parts[i][2:]
            else:
                parts[i] = '%' + h.upper() + parts[i][2:]
        else:
            parts[i] = '%' + parts[i]
    return ''.join(parts)


def requote_url(url):
    '''Re-quote the given URL.

    This function passes the given URL through an unquote/quote cycle to
    ensure that it is fully and consistently quoted.

    Calling this function multiple times on the url doesn't have any
    additional effect.
    '''
    # Unquote only the unreserved characters
    # Then quote only illegal characters (do not quote reserved, unreserved,
    # or '%')
    assert isinstance(url, str), 'requote_url expects url to be str'
    return urllib.quote(_unquote_unreserved(url), safe="!#$%&'()*+,/:;=?@[]~")


def requote_ajax(fragment):
    '''Ajax part escaping escaping.
    https://developers.google.com/webmasters/ajax-crawling/docs/specification
    '''
    fragment = fragment.replace('%', '%25').replace('#', '%23')
    fragment = fragment.replace('&', '%26').replace('+', '%2B')
    return fragment


def path_to_file_uri(path):
    '''Convert local filesystem path to legal File URIs as described in:
    http://en.wikipedia.org/wiki/File_URI_scheme
    '''
    x = urllib.pathname2url(os.path.abspath(path))
    if os.name == 'nt':
        x = x.replace('|', ':')  # http://bugs.python.org/issue5861
    return 'file:///%s' % x.lstrip('/')


def file_uri_to_path(uri):
    '''Convert File URI to local filesystem path according to:
    http://en.wikipedia.org/wiki/File_URI_scheme
    '''
    return urllib.url2pathname(urlparse(uri).path)


def any_to_uri(uri_or_path):
    '''Return an intelligently created valid URI.

    - if given an uri with a scheme, return it unmodified
    - if given a path name, return its File URI
    - otherwise append `http://` scheme.
    '''
    if os.path.splitdrive(uri_or_path)[0]:
        return path_to_file_uri(uri_or_path)
    u = urlparse(uri_or_path)
    if u.scheme:
        return uri_or_path
    if os.path.exists(uri_or_path):
        return path_to_file_uri(uri_or_path)
    # supposing the simplified url was given (e.g. www.google.com), simply
    # append 'http://' and see what happens
    return 'http://' + uri_or_path


def is_url(url):
    '''Return `True` if url has a correct scheme.
    '''
    return url.partition('://')[0] in ('file', 'http', 'https')


def is_url_from_any_domain(url, domains):
    '''Return `True` if given url matches any of the `domains`.
    '''
    host = urlparse(url).netloc
    if host:
        return any((host == d) or (host.endswith('.%s' % d)) for d in domains)
    else:
        return False


_utm_tags_re = re.compile('|'.join(['utm_source', 'utm_medium', 'utm_campaign',
                                    'utm_term', 'utm_content']))

def canonicalize_url(url, keep_blank_values=True, keep_fragments=False,
                     strip_utm_tags=True, encoding=None):
    '''Canonicalize the given url by applying the following procedures:

    - sort query arguments, first by key, then by value
    - percent encode paths and query arguments. non-ASCII characters are
      percent-encoded using UTF-8 (RFC-3986)
    - normalize all spaces (in query arguments) '+' (plus symbol)
    - normalize percent encodings case (%2f -> %2F)
    - remove query arguments with blank values (unless keep_blank_values is True)
    - remove fragments (unless keep_fragments is True)
    '''
    def _strip_tags(keyvals):
        return filter(lambda (k, v): not _utm_tags_re.match(k), keyvals)

    if isinstance(url, basestring):
        url = to_str(url, encoding)
    else:
        raise TypeError('Bad type for `url` object: %s' % type(url))

    scheme, netloc, path, params, query, fragment = urlparse(url)
    keyvals = parse_qsl(query, keep_blank_values)
    keyvals.sort()
    if strip_utm_tags:
        keyvals = _strip_tags(keyvals)
    query = urllib.urlencode(keyvals)
    if not path:
        path = '/'
    fragment = '' if not keep_fragments else fragment
    # sometimes utm tags are inside fragment
    if fragment and strip_utm_tags:
        try:
            parsed_fragment = parse_qsl(fragment, keep_blank_values=True, strict_parsing=True)
            fragment = urllib.urlencode(_strip_tags(parsed_fragment))
        except ValueError:
            pass
    return requote_url(urlunparse([scheme, netloc.lower(), path, params, query, fragment]))
