import lxml.html

from crawlmi.http import HtmlResponse


def get_html(response_or_str, encoding='utf-8', base_url=None):
    '''Bacause of lxml's annoying error:
        "ValueError: Unicode strings with encoding declaration are not supported."
    it can be a hassle to create etree correctly. This method solves it.
    '''
    if (not isinstance(response_or_str, HtmlResponse) and
            not isinstance(response_or_str, basestring)):
        raise TypeError('HtmlResponse or basestring expected.')

    if isinstance(response_or_str, HtmlResponse):
        body = response_or_str.text.encode('utf-8')
        encoding = 'utf-8'
        base_url = base_url or response_or_str.url
    elif isinstance(response_or_str, unicode):
        body = response_or_str.encode('utf-8')
        encoding = 'utf-8'
    else:
        body = response_or_str

    body = body or '<html/>'  # empty body raises error in lxml
    parser = lxml.html.HTMLParser(recover=True, encoding=encoding)
    return lxml.html.fromstring(body, parser=parser, base_url=base_url)
