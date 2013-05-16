from crawlmi import log

from crawlmi.http import TextResponse


class Filter(object):
    def __init__(self, engine):
        self.stats = engine.stats
        self.settings = engine.settings

    def process_request(self, request):
        url_limit = self.settings.get('FILTER_URL_LENGTH_LIMIT',
                                      req_or_resp=request)
        if url_limit and len(request.url) > url_limit:
            self.stats.inc_value('filter/url_limit')
            log.msg(format='Filtering request (url length %(length)d): %(url)s',
                    level=log.DEBUG,
                    length=len(request.url),
                    url=request.url)
            return

        filter_schemes = self.settings.get('FILTER_SCHEMES',
                                           req_or_resp=request)
        if request.parsed_url.scheme in filter_schemes:
            self.stats.inc_value('filter/bad_scheme')
            log.msg(format='Filtering request with bad scheme: %(url)s',
                    level=log.DEBUG,
                    url=request.url)
            return
        return request

    def process_response(self, response):
        filter_non_200 = self.settings.get('FILTER_NON_200_RESPONSE_STATUS',
                                           req_or_resp=response)
        if filter_non_200 and response.status != 200:
            self.stats.inc_value('filter/non_200')
            log.msg(format='Filtering non-200 response (status %(status)d): %(url)s',
                    level=log.DEBUG,
                    status=response.status,
                    url=response.url)
            return

        filter_status = self.settings.get('FILTER_RESPONSE_STATUS',
                                          req_or_resp=response)
        if filter_status(response.status):
            self.stats.inc_value('filter/bad_status')
            log.msg(format='Filtering response with bad status (status %(status)d): %(url)s',
                    level=log.DEBUG,
                    status=response.status,
                    url=response.url)
            return

        filter_nontext = self.settings.get_bool('FILTER_NONTEXT_RESPONSE',
                                                req_or_resp=response)
        if filter_nontext and not isinstance(response, TextResponse):
            self.stats.inc_value('filter/non_text')
            log.msg(format='Filtering nontext response: %(url)s',
                    level=log.DEBUG,
                    url=response.url)
            return

        return response
