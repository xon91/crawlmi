from crawlmi.http.headers import Headers


_no_request_error = 'Response is not tied to any request.'


class Response(object):
    def __init__(self, url, status=200, headers={}, body=None, request=None):
        self.url = url
        self.status = int(status)
        self.headers = Headers(headers)
        self.body = body or ''
        self.request = request

    def __repr__(self):
        return '<Response [%s]>' % (self.status)

    @property
    def meta(self):
        try:
            return self.request.meta
        except AttributeError:
            raise AttributeError('Response.meta unavailable. %s' %
                                 _no_request_error)

    @property
    def history(self):
        try:
            return self.request.history
        except AttributeError:
            raise AttributeError('Response.history unavailable. %s' %
                                 _no_request_error)

    @property
    def original_url(self):
        try:
            return self.request.original_url
        except AttributeError:
            raise AttributeError('Response.original_url unavailable. %s' %
                                 _no_request_error)
