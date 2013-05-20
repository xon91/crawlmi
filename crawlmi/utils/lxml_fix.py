import lxml.html

from crawlmi.http import TextResponse


def get_html(response_or_text):
    if isinstance(response_or_text, TextResponse):
        utf8_body = response_or_text.text.encode('utf-8')
    elif isinstance(response_or_text, unicode):
        utf8_body = response_or_text.encode('utf-8')
    else:
        raise TypeError('Expecting TextResponse or unicode object.')
    parser = lxml.html.HTMLParser(recover=True, encoding='utf-8')
    return lxml.html.fromstring(utf8_body, parser=parser)
