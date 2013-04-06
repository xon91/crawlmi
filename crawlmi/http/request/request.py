from urlparse import urlparse, urlunparse
from urllib import urlencode

from crawlmi.http import Headers
from crawlmi.utils.python import to_str
from crawlmi.utils.url import requote_url, requote_ajax


class Request(object):
    def __init__(self, url, callback=None, method='GET', headers={},
                 params={}, body='', meta={}, errback=None, proxy=None,
                 priority=0, history=[], encoding='utf-8'):
        self.callback = callback
        self.errback = errback

        self.headers = Headers(headers, encoding)
        self.meta = dict(meta)
        self.history = list(history)
        self.proxy = proxy
        self.priority = priority

        # following attributes are immutable
        self._encoding = encoding
        self._method = self._prepare_method(method)
        self._url = self._prepare_url(url, params)
        self._body = self._prepare_body(body)

    def __repr__(self):
        return '<Request [%s] %s>' % (self._method, self._url)

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method

    @property
    def body(self):
        return self._body

    @property
    def encoding(self):
        return self._encoding

    @property
    def details(self):
        '''Useful for debugging purposes.'''
        return '<Request [%s] %s> (Headers: %s, History: %s, Meta: %s, Proxy: %s)' % \
            (self._method, self._url, self.headers, self.meta, self.proxy)

    @property
    def original_url(self):
        return self.history[0] if self.history else self._url

    def _prepare_method(self, method):
        return str(method).upper()

    def _prepare_url(self, url, params):
        if isinstance(url, basestring):
            url = to_str(url, self._encoding)
        else:
            raise TypeError('Bad type for `url` object: %s' % type(url))

        scheme, netloc, path, _params, query, fragment = urlparse(url)
        if not scheme:
            raise ValueError('Invalid URL %s: No schema supplied.' % url)
        if not netloc and not path:
            raise ValueError('Invalid URL %s: No netloc nor path supplied.' %
                             url)

        # Bare domains aren't valid URLs.
        if not path:
            path = '/'

        enc_params = self._encode_params(params)
        if enc_params:
            if query:
                query = '%s&%s' % (query, enc_params)
            else:
                query = enc_params

        # ajax excaping
        if fragment.startswith('!'):
            fragment = requote_ajax(fragment[1:])
            if query:
                query = '%s&_escaped_fragment_=%s' % (query, fragment)
            else:
                query = '_escaped_fragment_=%s' % fragment
            fragment = ''

        quoted = requote_url(urlunparse([scheme, netloc, path, _params, query,
                                         fragment]))
        self.parsed_url = urlparse(quoted)
        return quoted

    def _encode_params(self, data):
        '''Encode parameters in a piece of data.

        Will successfully encode parameters when passed as a dict or a list of
        2-tuples. Order is retained if data is a list of 2-tuples but abritrary
        if parameters are supplied as a dict.
        '''
        if isinstance(data, basestring):
            return to_str(data, self._encoding)
        elif hasattr(data, '__iter__'):
            result = []
            if isinstance(data, dict):
                items = data.iteritems()
            else:
                items = data
            for k, vs in items:
                if not hasattr(vs, '__iter__'):
                    vs = [vs]
                for v in vs:
                    if v is not None:
                        result.append((to_str(k, self._encoding),
                                       to_str(v, self._encoding)))
            return urlencode(result, doseq=True)
        else:
            raise TypeError('Bad type for `params` object: %s' % type(data))

    def _prepare_body(self, body):
        return to_str(body, self._encoding)

    def copy(self):
        '''Return a copy of this Request.'''
        return self.replace()

    def replace(self, *args, **kwargs):
        '''Create a new Request with the same attributes except for those
        given new values.
        '''
        for x in ['url', 'callback', 'errback', 'method', 'headers', 'priority',
                  'meta', 'body', 'proxy', 'history', 'encoding']:
            kwargs.setdefault(x, getattr(self, x))
        cls = kwargs.pop('cls', self.__class__)
        return cls(*args, **kwargs)
