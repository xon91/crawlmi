from crawlmi.http.response import Response
from crawlmi.utils.encoding import get_unicode_from_response


class TextResponse(Response):
    def __init__(self, *args, **kwargs):
        super(TextResponse, self).__init__(*args, **kwargs)
        self._encoding = None
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
        self._encoding, self._unicode_body = get_unicode_from_response(self)
