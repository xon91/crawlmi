from crawlmi.utils.request import request_http_repr
from crawlmi.utils.response import response_http_repr


class DownloaderStats(object):
    def __init__(self, engine):
        self.stats = engine.stats

    def process_request(self, request):
        self.stats.inc_value('downloader/request_count')
        self.stats.inc_value('downloader/request_method_count/%s' % request.method)
        req_len = len(request_http_repr(request))
        self.stats.inc_value('downloader/request_bytes', req_len)
        return request

    def process_response(self, response):
        self.stats.inc_value('downloader/response_count')
        self.stats.inc_value('downloader/response_status_count/%s' % response.status)
        resp_len = len(response_http_repr(response))
        self.stats.inc_value('downloader/response_bytes', resp_len)
        return response

    def process_failure(self, failure):
        exception = failure.value
        ex_class = "%s.%s" % (exception.__class__.__module__, exception.__class__.__name__)
        self.stats.inc_value('downloader/exception_count')
        self.stats.inc_value('downloader/exception_type_count/%s' % ex_class)
        return failure
