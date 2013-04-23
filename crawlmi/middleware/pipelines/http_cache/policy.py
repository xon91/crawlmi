from email.utils import mktime_tz, parsedate_tz
from time import time
from weakref import WeakKeyDictionary


class DummyPolicy(object):
    def __init__(self, settings):
        self.ignore_schemes = settings.get_list('HTTP_CACHE_IGNORE_SCHEMES')
        self.ignore_non_200 = settings.get_bool('HTTP_CACHE_IGNORE_NON_200_STATUS')
        self.ignore_status = settings.get('HTTP_CACHE_IGNORE_STATUS')

    def should_cache_request(self, request):
        return request.parsed_url.scheme not in self.ignore_schemes

    def should_cache_response(self, response, request):
        if self.ignore_non_200 and response.status != 200:
            return False
        return not self.ignore_status(response.status)

    def is_cached_response_fresh(self, response, request):
        return True

    def is_cached_response_valid(self, cachedresponse, response, request):
        return True


class RFC2616Policy(object):
    MAXAGE = 3600 * 24 * 365  # one year

    def __init__(self, settings):
        self.ignore_schemes = settings.get_list('HTTP_CACHE_IGNORE_SCHEMES')
        self._cc_parsed = WeakKeyDictionary()

    def _parse_cachecontrol(self, r):
        if r not in self._cc_parsed:
            cch = r.headers.get('Cache-Control', '')
            self._cc_parsed[r] = parse_cachecontrol(cch)
        return self._cc_parsed[r]

    def should_cache_request(self, request):
        if request.parsed_url.scheme in self.ignore_schemes:
            return False
        cc = self._parse_cachecontrol(request)
        # obey user-agent directive 'Cache-Control: no-store'
        if 'no-store' in cc:
            return False
        # Any other is eligible for caching
        return True

    def should_cache_response(self, response, request):
        # What is cacheable - http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html#sec14.9.1
        # Response cacheability - http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html#sec13.4
        # Status code 206 is not included because cache can not deal with partial contents
        cc = self._parse_cachecontrol(response)
        # obey directive 'Cache-Control: no-store'
        if 'no-store' in cc:
            return False
        # Never cache 304 (Not Modified) responses
        elif response.status == 304:
            return False
        # Any hint on response expiration is good
        elif 'max-age' in cc or 'Expires' in response.headers:
            return True
        # Firefox fallbacks this statuses to one year expiration if none is set
        elif response.status in (300, 301, 308):
            return True
        # Other statuses without expiration requires at least one validator
        elif response.status in (200, 203, 401):
            return 'Last-Modified' in response.headers or 'ETag' in response.headers
        # Any other is probably not eligible for caching
        # Makes no sense to cache responses that does not contain expiration
        # info and can not be revalidated
        else:
            return False

    def is_cached_response_fresh(self, cachedresponse, request):
        cc = self._parse_cachecontrol(cachedresponse)
        ccreq = self._parse_cachecontrol(request)
        if 'no-cache' in cc or 'no-cache' in ccreq:
            return False

        now = time()
        freshnesslifetime = self._compute_freshness_lifetime(cachedresponse, request, now)
        currentage = self._compute_current_age(cachedresponse, request, now)
        if currentage < freshnesslifetime:
            return True
        # Cached response is stale, try to set validators if any
        self._set_conditional_validators(request, cachedresponse)
        return False

    def is_cached_response_valid(self, cachedresponse, response, request):
        return response.status == 304

    def _set_conditional_validators(self, request, cachedresponse):
        if 'Last-Modified' in cachedresponse.headers:
            request.headers['If-Modified-Since'] = cachedresponse.headers['Last-Modified']

        if 'ETag' in cachedresponse.headers:
            request.headers['If-None-Match'] = cachedresponse.headers['ETag']

    def _compute_freshness_lifetime(self, response, request, now):
        # Reference nsHttpResponseHead::ComputeFresshnessLifetime
        # http://dxr.mozilla.org/mozilla-central/netwerk/protocol/http/nsHttpResponseHead.cpp.html#l259
        cc = self._parse_cachecontrol(response)
        if 'max-age' in cc:
            try:
                return max(0, int(cc['max-age']))
            except ValueError:
                pass

        # Parse date header or synthesize it if none exists
        date = rfc1123_to_epoch(response.headers.get('Date')) or now

        # Try HTTP/1.0 Expires header
        if 'Expires' in response.headers:
            expires = rfc1123_to_epoch(response.headers['Expires'])
            # When parsing Expires header fails RFC 2616 section 14.21 says we
            # should treat this as an expiration time in the past.
            return max(0, expires - date) if expires else 0

        # Fallback to heuristic using last-modified header
        # This is not in RFC but on Firefox caching implementation
        lastmodified = rfc1123_to_epoch(response.headers.get('Last-Modified'))
        if lastmodified and lastmodified <= date:
            return (date - lastmodified) / 10

        # This request can be cached indefinitely
        if response.status in (300, 301, 308):
            return self.MAXAGE

        # Insufficient information to compute fresshness lifetime
        return 0

    def _compute_current_age(self, response, request, now):
        # Reference nsHttpResponseHead::ComputeCurrentAge
        # http://dxr.mozilla.org/mozilla-central/netwerk/protocol/http/nsHttpResponseHead.cpp.html
        currentage = 0
        # If Date header is not set we assume it is a fast connection, and
        # clock is in sync with the server
        date = rfc1123_to_epoch(response.headers.get('Date')) or now
        if now > date:
            currentage = now - date

        if 'Age' in response.headers:
            try:
                age = int(response.headers['Age'])
                currentage = max(currentage, age)
            except ValueError:
                pass

        return currentage


def parse_cachecontrol(header):
    '''Parse Cache-Control header:
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9

    >>> cachecontrol_directives('public, max-age=3600')
    {'public': None, 'max-age': '3600'}
    >>> cachecontrol_directives('')
    {}
    '''
    directives = {}
    for directive in header.split(','):
        key, sep, val = directive.strip().partition('=')
        if key:
            directives[key.lower()] = val if sep else None
    return directives


def rfc1123_to_epoch(date_str):
    try:
        return mktime_tz(parsedate_tz(date_str))
    except Exception:
        return None
