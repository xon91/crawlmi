from twisted.web.http import RESPONSES

from crawlmi.http import Headers


_no_request_error = 'Response is not tied to any request.'


class Response(object):
    def __init__(self, url, status=200, headers={}, body=None, request=None):
        self.url = url
        self.status = int(status)
        self.headers = Headers(headers)
        self.request = request

        # following attributes are immutable
        self._body = body or ''

    def __repr__(self):
        msg = RESPONSES.get(self.status)
        if msg:
            return '<%s [%s (%s)]>' % (self.__class__.__name__, self.status, msg)
        else:
            return '<%s [%s]>' % (self.__class__.__name__, self.status)

    @property
    def body(self):
        return self._body

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

    def copy(self):
        '''Return a copy of this Response.'''
        return self.replace()

    def replace(self, *args, **kwargs):
        '''Create a new Response with the same attributes except for those
        given new values.
        '''
        for x in ['url', 'status', 'headers', 'request', 'body']:
            kwargs.setdefault(x, getattr(self, x))
        cls = kwargs.pop('cls', self.__class__)
        return cls(*args, **kwargs)
