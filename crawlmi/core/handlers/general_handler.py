from crawlmi.exceptions import NotConfigured, NotSupported
from crawlmi.utils.misc import load_object


class GeneralHandler(object):
    '''Based on url schema decides which specialized handler to use.'''

    def __init__(self, settings):
        self._handlers = {}
        self._not_configured = {}
        handlers = settings.get('DOWNLOAD_HANDLERS_BASE', {})
        for scheme, clspath in handlers.iteritems():
            cls = load_object(clspath)
            try:
                dh = cls(settings)
            except NotConfigured as e:
                self._not_configured[scheme] = str(e)
            else:
                self._handlers[scheme] = dh

    def download_request(self, request):
        return self._get_handler(request).download_request(request)

    def _get_handler(self, request):
        try:
            handler = self._handlers[request.parsed_url.scheme]
        except KeyError:
            msg = self._not_configured.get(
                request.parsed_url.scheme,
                'no handler available for that scheme')
            raise NotSupported('Unsupported URL scheme `%s`: %s' %
                               (request.parsed_url.scheme, msg))
        return handler
