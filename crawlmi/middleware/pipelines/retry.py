'''
An extension to retry failed requests that are potentially caused by temporary
problems such as a connection timeout or HTTP 500 error.

You can change the behaviour of this middleware by modifing the scraping settings:
RETRY_TIMES - how many times to retry a failed page
RETRY_HTTP_CODES - which HTTP response codes to retry

Failed pages are collected on the scraping process and rescheduled at the end,
once the spider has finished crawling all regular (non failed) pages.

About HTTP errors to consider:

- You may want to remove 400 from RETRY_HTTP_CODES, if you stick to the HTTP
  protocol. It's included by default because it's a common code used to
  indicate server overload, which would be something we want to retry
'''

import zlib

from twisted.internet.error import (TimeoutError as ServerTimeoutError,
    DNSLookupError, ConnectionRefusedError, ConnectionDone, ConnectError,
    ConnectionLost, TCPTimedOutError)
from twisted.internet.defer import TimeoutError as UserTimeoutError

from crawlmi import log
from crawlmi.core.webclient import BadHttpHeaderError


class Retry(object):
    # IOError is raised by the HttpCompression middleware when trying to
    # decompress an empty response
    EXCEPTIONS_TO_RETRY = (UserTimeoutError, ServerTimeoutError,
        ConnectionRefusedError, ConnectionDone, ConnectError, ConnectionLost,
        TCPTimedOutError, DNSLookupError, IOError, zlib.error,
        BadHttpHeaderError)

    def __init__(self, engine):
        settings = engine.settings
        self.max_retry_times = settings.get_int('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in
                                    settings.get_list('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.get_int('RETRY_PRIORITY_ADJUST')

    def process_response(self, response):
        if response.status in self.retry_http_codes:
            reason = response.status_message
            return self._retry(response.request, reason) or response
        return response

    def process_failure(self, failure):
        exception = failure.value
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            return self._retry(failure.request, exception) or failure
        return failure

    def _retry(self, request, reason):
        retries = request.meta.get('retry_times', 0) + 1

        if retries <= self.max_retry_times:
            log.msg(format='Retrying %(request)s (failed %(retries)d times): %(reason)s',
                    level=log.DEBUG, request=request, retries=retries,
                    reason=reason)
            retry_req = request.copy()
            retry_req.meta['retry_times'] = retries
            retry_req.meta['DUPLICATE_FILTER_ENABLED'] = False
            retry_req.priority = request.priority + self.priority_adjust
            return retry_req
        else:
            log.msg(format='Gave up retrying %(request)s (failed %(retries)d times): %(reason)s',
                    level=log.DEBUG, request=request, retries=retries,
                    reason=reason)
