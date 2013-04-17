from crawlmi import log

from crawlmi.http import TextResponse


class Filter(object):
    def __init__(self, engine):
        self.stats = engine.stats
        self.filter_nontext = engine.settings.get_bool('FILTER_NONTEXT_RESPONSE')
        self.url_limit = engine.settings.get_int('FILTER_URL_LENGTH_LIMIT')
        self.filter_non_200 = engine.settings.get_bool('FILTER_NON_200_RESPONSE_STATUS')
        self.filter_status = engine.settings.get('FILTER_RESPONSE_STATUS')

    def process_request(self, request):
        if self.url_limit and len(request.url) > self.url_limit:
            self.stats.inc_value('filter/url_limit')
            log.msg(format='Filtering request (url length %(length)d): %(url)s',
                    level=log.DEBUG,
                    length=len(request.url),
                    url=request.url)
            return
        return request

    def process_response(self, response):
        if self.filter_non_200 and response.status != 200:
            self.stats.inc_value('filter/non_200')
            log.msg(format='Filtering non-200 response (status %(status)d): %(url)s',
                    level=log.DEBUG,
                    status=response.status,
                    url=response.url)
            return

        if self.filter_status(response.status):
            self.stats.inc_value('filter/bad_status')
            log.msg(format='Filtering response with bad status (status %(status)d): %(url)s',
                    level=log.DEBUG,
                    status=response.status,
                    url=response.url)
            return

        if self.filter_nontext and not isinstance(response, TextResponse):
            self.stats.inc_value('filter/non_text')
            log.msg(format='Filtering nontext response: %(url)s',
                    level=log.DEBUG,
                    url=response.url)
            return

        return response
