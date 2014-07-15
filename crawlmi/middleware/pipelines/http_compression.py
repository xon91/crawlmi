import zlib

from crawlmi.exceptions import DecompressSizeError
from crawlmi.http.response import factory
from crawlmi.utils.gz import gunzip, is_gzipped


class HttpCompression(object):
    '''Allows compressed (gzip, deflate) traffic to be received from web sites.
    '''

    def __init__(self, engine):
        self.settings = engine.settings

    def process_request(self, request):
        request.headers.setdefault('Accept-Encoding', 'gzip,deflate')
        return request

    def process_response(self, response):
        content_encoding = response.headers.getlist('Content-Encoding')
        if content_encoding and not is_gzipped(response):
            max_length = self.settings.get_int('DOWNLOAD_SIZE_LIMIT', 0,
                                               response.request)
            encoding = content_encoding.pop()
            if not content_encoding:
                del response.headers['Content-Encoding']
            decoded_body = self._decode(response.body, encoding.lower(),
                                        max_length)
            resp_cls = factory.from_args(headers=response.headers,
                                         url=response.url)
            response = response.replace(cls=resp_cls, body=decoded_body)
        return response

    def _decode(self, body, encoding, max_length=0):
        if encoding == 'gzip' or encoding == 'x-gzip':
            body = gunzip(body, max_length)
        elif encoding == 'deflate':
            try:
                if max_length:
                    dobj = zlib.decompressobj()
                    body = dobj.decompress(body, max_length)
                    if dobj.unconsumed_tail:
                        raise DecompressSizeError(
                            'Response exceeded %s bytes' % max_length)
                else:
                    body = zlib.decompress(body)
            except zlib.error:
                # ugly hack to work with raw deflate content that may
                # be sent by microsoft servers. For more information, see:
                # http://carsten.codimi.de/gzip.yaws/
                # http://www.port80software.com/200ok/archive/2005/10/31/868.aspx
                # http://www.gzip.org/zlib/zlib_faq.html#faq38
                if max_length:
                    dobj = zlib.decompressobj(-15)
                    body = dobj.decompress(body, max_length)
                    if dobj.unconsumed_tail:
                        raise DecompressSizeError(
                            'Response exceeded %s bytes' % max_length)
                else:
                    body = zlib.decompress(body, -15)
        return body
