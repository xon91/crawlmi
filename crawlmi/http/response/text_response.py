from crawlmi.http import Response
from crawlmi.utils.encoding import get_unicode_from_response


class TextResponse(Response):
    def __init__(self, *args, **kwargs):
        self._encoding = kwargs.pop('encoding', None)
        super(TextResponse, self).__init__(*args, **kwargs)
        self._unicode_body = None

    @property
    def text(self):
        if self._unicode_body is None:
            self._prepare_unicode_body()
        return self._unicode_body

    @property
    def encoding(self):
        if self._encoding is None:
            self._prepare_unicode_body()
        return self._encoding

    def _prepare_unicode_body(self):
        if self._encoding is None:
            self._encoding, self._unicode_body = get_unicode_from_response(self)
        else:
            self._unicode_body = unicode(self.body, self._encoding, 'replace')

    def replace(self, *args, **kwargs):
        obj = super(TextResponse, self).replace(*args, **kwargs)
        # try to copy encoding and unicode budy, for better performance
        if ((self._encoding == obj._encoding or obj._encoding is None) and
                self.body == obj.body):
            obj._encoding = self._encoding
            obj._unicode_body = self._unicode_body
        return obj
