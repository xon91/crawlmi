from mimetypes import MimeTypes
from os import path

from crawlmi.http import Response, TextResponse, XmlResponse, HtmlResponse
from crawlmi.utils.python import is_binary


_mime_types = MimeTypes()
_mt_filename = path.join(path.dirname(path.abspath(__file__)), 'mime.types')
with open(_mt_filename, 'rb') as f:
    _mime_types.readfp(f)

_response_classes = {
    'text/html': HtmlResponse,
    'application/atom+xml': XmlResponse,
    'application/rdf+xml': XmlResponse,
    'application/rss+xml': XmlResponse,
    'application/xhtml+xml': HtmlResponse,
    'application/vnd.wap.xhtml+xml': HtmlResponse,
    'application/xml': XmlResponse,
    'application/json': TextResponse,
    'application/javascript': TextResponse,
    'application/x-javascript': TextResponse,
    'text/xml': XmlResponse,
    'text/*': TextResponse,
}


def from_mime_type(mime_type):
    '''Return the most appropiate Response class for the given mime type.'''
    if mime_type is None:
        return Response
    elif mime_type in _response_classes:
        return _response_classes[mime_type]
    else:
        basetype = '%s/*' % mime_type.split('/')[0]
        return _response_classes.get(basetype, Response)


def from_filename(filename):
    '''Return the most appropiate Response class from a filename.'''
    mime_type, encoding = _mime_types.guess_type(filename)
    if mime_type and not encoding:
        return from_mime_type(mime_type)
    else:
        return Response


def from_body(body):
    '''Try to guess the appropiate response based on the body content.
    This method is a bit magic and could be improved in the future, but
    it's not meant to be used except for special cases where response types
    cannot be guess using more straightforward methods.
    '''
    chunk = body[:5000]
    if is_binary(chunk):
        return from_mime_type('application/octet-stream')
    elif '<html>' in chunk.lower():
        return from_mime_type('text/html')
    elif '<?xml' in chunk.lower():
        return from_mime_type('text/xml')
    else:
        return from_mime_type('text')


def from_content_type(content_type, content_encoding=None):
    '''Return the most appropiate Response class from an HTTP Content-Type
    header.
    '''
    if content_encoding:
        return Response
    mime_type = content_type.split(';')[0].strip().lower()
    return from_mime_type(mime_type)


def from_content_disposition(content_disposition):
    try:
        filename = content_disposition.split(';')[1].split('=')[1]
        filename = filename.strip('"\'')
        return from_filename(filename)
    except IndexError:
        return Response


def from_headers(headers):
    '''Return the most appropiate Response class by looking at the HTTP
    headers.
    '''
    cls = Response
    if 'Content-Type' in headers:
        cls = from_content_type(headers['Content-type'],
                                headers.get('Content-Encoding'))
    if cls is Response and 'Content-Disposition' in headers:
        cls = from_content_disposition(headers['Content-Disposition'])
    return cls


def from_args(headers=None, url=None, filename=None, body=None):
    '''Guess the most appropiate Response class based on the given arguments.
    '''
    cls = Response
    if headers is not None:
        cls = from_headers(headers)
    if cls is Response and url is not None:
        cls = from_filename(url)
    if cls is Response and filename is not None:
        cls = from_filename(filename)
    if cls is Response and body is not None:
        cls = from_body(body)
    return cls
