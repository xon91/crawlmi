import os
import tempfile
import webbrowser

from crawlmi.http.response import HtmlResponse, TextResponse


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
