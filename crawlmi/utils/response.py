import os
import tempfile
import webbrowser

from twisted.web.http import RESPONSES

from crawlmi.http.response import HtmlResponse, TextResponse


def response_http_repr(response):
    '''Return raw HTTP representation (as string) of the given response. This
    is provided only for reference, since it's not the exact stream of bytes
    that was received (that's not exposed by Twisted).
    '''

    s = 'HTTP/1.1 %d %s\r\n' % (response.status, RESPONSES.get(response.status, ''))
    if response.headers:
        s += response.headers.to_string() + '\r\n'
    s += '\r\n'
    s += response.body
    return s


def open_in_browser(response, _openfunc=webbrowser.open):
    '''Open the given response in a local web browser, populating the <base>
    tag for external links to work.
    '''
    body = response.body
    if isinstance(response, HtmlResponse):
        if '<base' not in body:
            body = body.replace('<head>', '<head><base href="%s">' % response.url)
        ext = '.html'
    elif isinstance(response, TextResponse):
        ext = '.txt'
    else:
        raise TypeError('Unsupported response type: %s' %
                        response.__class__.__name__)
    fd, fname = tempfile.mkstemp(ext)
    os.write(fd, body)
    os.close(fd)
    return _openfunc('file://%s' % fname)
