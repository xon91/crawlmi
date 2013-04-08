from email.utils import formatdate

from crawlmi import signals
from crawlmi.utils.misc import load_object


class HttpCache(object):

    def __init__(self, engine):
        settings = engine.settings
        self.policy = load_object(settings['HTTPCACHE_POLICY'])(settings)
        self.storage = load_object(settings['HTTPCACHE_STORAGE'])(engine)
        self.ignore_missing = settings.get_bool('HTTPCACHE_IGNORE_MISSING')
        self.stats = engine.stats

        engine.signals.connect(self.engine_started, signal=signals.engine_started)
        engine.signals.connect(self.engine_stopping, signal=signals.engine_stopping)

    def engine_started(self):
        self.storage.open()

    def engine_stopping(self):
        self.storage.close()

    def process_request(self, request):
        # Skip uncacheable requests
        if not self.policy.should_cache_request(request):
            request.meta['_dont_cache'] = True  # flag as uncacheable
            return request

        # Look for cached response and check if expired
        cached_response = self.storage.retrieve_response(request)
        if cached_response is None:
            self.stats.inc_value('httpcache/miss')
            if self.ignore_missing:
                self.stats.inc_value('httpcache/ignore')
                return
            return request  # first time request
        cached_response.flags.append('cached')

        # Return cached response only if not expired
        if self.policy.is_cached_response_fresh(cached_response, request):
            self.stats.inc_value('httpcache/hit')
            return cached_response

        # Keep a reference to cached response to avoid a second cache lookup on
        # process_response hook
        request.meta['cached_response'] = cached_response
        return request

    def process_response(self, response):
        request = response.request
        # Skip uncacheable requests
        if '_dont_cache' in request.meta:
            request.meta.pop('_dont_cache')
            return response

        # RFC2616 requires origin server to set Date header,
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.18
        if 'Date' not in response.headers:
            response.headers['Date'] = formatdate(usegmt=1)

        # Do not validate first-hand responses
        cached_response = request.meta.pop('cached_response', None)
        if cached_response is None:
            self.stats.inc_value('httpcache/firsthand')
            self._cache_response(response, request, cached_response)
            return response

        if self.policy.is_cached_response_valid(cached_response, response, request):
            self.stats.inc_value('httpcache/revalidate')
            return cached_response

        self.stats.inc_value('httpcache/invalidate')
        self._cache_response(response, request, cached_response)
        return response

    def _cache_response(self, response, request, cached_response):
        if self.policy.should_cache_response(response, request):
            self.stats.inc_value('httpcache/store')
            self.storage.store_response(request, response)
        else:
            self.stats.inc_value('httpcache/uncacheable')
