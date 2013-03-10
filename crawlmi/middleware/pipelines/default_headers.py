class DefaultHeaders(object):
    '''Use default HTTP headers in requests.
    '''

    def __init__(self, engine):
        self.headers = engine.settings.get('DEFAULT_REQUEST_HEADERS')

    def process_request(self, request):
        for k, v in self.headers.iteritems():
            request.headers.setdefault(k, v)
        return request
