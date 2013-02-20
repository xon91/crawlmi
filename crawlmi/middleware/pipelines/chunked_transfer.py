class ChunkedTransfer(object):
    '''Adds support for chunked transfer encoding. See:
    http://en.wikipedia.org/wiki/Chunked_transfer_encoding
    '''

    def __init__(self, engine):
        pass

    def process_response(self, response):
        if response.headers.get('Transfer-Encoding') == 'chunked':
            body = self._decode_chunked_transfer(response.body)
            return response.replace(body=body)
        return response

    def _decode_chunked_transfer(self, chunked_body):
        body, h, t = '', '', chunked_body
        while t:
            h, t = t.split('\r\n', 1)
            if h == '0':
                break
            size = int(h, 16)
            body += t[:size]
            t = t[size + 2:]
        return body
