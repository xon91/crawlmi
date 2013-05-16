from crawlmi.exceptions import DropRequest
from crawlmi.http import TextResponse


class FilterError(DropRequest):
    '''Raised when filtering out the request.'''


class Filter(object):
    def __init__(self, engine):
        self.stats = engine.stats
        self.settings = engine.settings

    def process_request(self, request):
        url_limit = self.settings.get('FILTER_URL_LENGTH_LIMIT',
                                      req_or_resp=request)
        if url_limit and len(request.url) > url_limit:
            self.stats.inc_value('filter/url_limit')
            raise FilterError('Url too long: %s' % len(request.url))

        filter_schemes = self.settings.get('FILTER_SCHEMES',
                                           req_or_resp=request)
        if request.parsed_url.scheme in filter_schemes:
            self.stats.inc_value('filter/bad_scheme')
            raise FilterError('Bad request scheme: %s' %
                              request.parsed_url.scheme)
        return request

    def process_response(self, response):
        filter_non_200 = self.settings.get('FILTER_NON_200_RESPONSE_STATUS',
                                           req_or_resp=response)
        if filter_non_200 and not (200 <= response.status < 300):
            self.stats.inc_value('filter/non_200')
            raise FilterError('Non-200 status: %s' % response.status)

        filter_status = self.settings.get('FILTER_RESPONSE_STATUS',
                                          req_or_resp=response)
        if filter_status(response.status):
            self.stats.inc_value('filter/bad_status')
            raise FilterError('Bad status: %s' % response.status)

        filter_nontext = self.settings.get_bool('FILTER_NONTEXT_RESPONSE',
                                                req_or_resp=response)
        if filter_nontext and not isinstance(response, TextResponse):
            self.stats.inc_value('filter/non_text')
            raise FilterError('Nontext response')

        return response
