from twisted.web.http import RESPONSES

from crawlmi.http import Headers
from crawlmi.utils.trackref import object_ref


_no_request_error = 'Response is not tied to any request.'


class Response(object_ref):
    def __init__(self, url, status=200, headers={}, body=None, request=None,
                 flags=None):
        self.url = url
        self.status = int(status)
        self.headers = Headers(headers)
        self.request = request
        self.flags = [] if flags is None else list(flags)

        # following attributes are immutable
        self._body = body or ''

    def __repr__(self):
        msg = ' (%s)' % self.status_message if self.status_message else ''
        flags = ' %s' % self.flags if self.flags else ''
        return '<%s %s [%s%s]>%s' % (self.__class__.__name__, self.url,
                                     self.status, msg, flags)

    @property
    def status_message(self):
        return RESPONSES.get(self.status, '')

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
        for x in ['url', 'status', 'headers', 'request', 'body', 'flags']:
            kwargs.setdefault(x, getattr(self, x))
        cls = kwargs.pop('cls', self.__class__)
        return cls(*args, **kwargs)
