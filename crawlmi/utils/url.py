from urllib import quote


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
                parts[i] = '%' + parts[i]
        else:
            parts[i] = '%' + parts[i]
    return ''.join(parts)


def requote_url(url):
    '''Re-quote the given URL.

    This function passes the given URL through an unquote/quote cycle to
    ensure that it is fully and consistently quoted.

    Calling this function multiple times on the url doesn't have any effect.
    '''
    # Unquote only the unreserved characters
    # Then quote only illegal characters (do not quote reserved, unreserved,
    # or '%')
    assert isinstance(url, str), 'requote_url expects url to be str'
    return quote(_unquote_unreserved(url), safe="!#$%&'()*+,/:;=?@[]~")


def requote_ajax(fragment):
    '''Ajax part escaping escaping.
    https://developers.google.com/webmasters/ajax-crawling/docs/specification
    '''
    fragment = fragment.replace('%', '%25').replace('#', '%23')
    fragment = fragment.replace('&', '%26').replace('+', '%2B')
    return fragment
