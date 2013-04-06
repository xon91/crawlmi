from crawlmi import log

from crawlmi.http import TextResponse


class Filter(object):
    def __init__(self, engine):
        self.body_limit = engine.settings.get_int('FILTER_BODY_LENGTH_LIMIT')
        self.filter_nontext = engine.settings.get_bool('FILTER_NONTEXT_RESPONSE')
        self.url_limit = engine.settings.get_int('FILTER_URL_LENGTH_LIMIT')
        self.filter_non_200 = engine.settings.get_bool('FILTER_NON_200_RESPONSE_STATUS')
        self.filter_status = engine.settings.get('FILTER_RESPONSE_STATUS')

    def process_request(self, request):
        if self.url_limit and len(request.url) > self.url_limit:
            log.msg(format='Filtering request (url length %(length)d): %(url)s',
                    level=log.DEBUG,
                    length=len(request.url),
                    url=request.url)
            return
        return request

    def process_response(self, response):
        if self.filter_non_200 and response.status != 200:
            log.msg(format='Filtering non-200 response (status %(status)d): %(url)s',
                    level=log.DEBUG,
                    status=response.status,
                    url=response.url)
            return

        if self.filter_status(response.status):
            log.msg(format='Filtering response with bad status (status %(status)d): %(url)s',
                    level=log.DEBUG,
                    status=response.status,
                    url=response.url)
            return

        if self.body_limit and len(response.body) > self.body_limit:
            log.msg(format='Filtering big response (body length %(length)d): %(url)s',
                    level=log.DEBUG,
                    length=len(response.body),
                    url=response.url)
            return

        if self.filter_nontext and not isinstance(response, TextResponse):
            log.msg(format='Filtering nontext response: %(url)s',
                    level=log.DEBUG,
                    url=response.url)
            return

        return response
