import os
from collections import defaultdict

from crawlmi import log
from crawlmi.http import Response
from crawlmi.http.cookies import CookieJar


class Cookies(object):
    '''Enables working with sites that require cookies.
    '''
    def __init__(self, engine):
        self.jars = defaultdict(CookieJar)
        self.debug = engine.settings.get_bool('COOKIES_DEBUG')

    def process_request(self, request):
        cookiejar_key = request.meta.get('cookiejar')
        jar = self.jars[cookiejar_key]
        cookies = self._get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)

        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        self._debug_cookie(request)
        return request

    def process_response(self, response):
        # extract cookies from Set-Cookie and drop invalid/expired cookies
        cookiejar_key = response.meta.get('cookiejar')
        jar = self.jars[cookiejar_key]
        jar.extract_cookies(response, response.request)
        self._debug_set_cookie(response)
        return response

    def _debug_cookie(self, request):
        if self.debug:
            cl = request.headers.getlist('Cookie')
            if cl:
                msg = 'Sending cookies to: %s' % request + os.linesep
                msg += os.linesep.join('Cookie: %s' % c for c in cl)
                log.msg(msg, level=log.DEBUG)

    def _debug_set_cookie(self, response):
        if self.debug:
            cl = response.headers.getlist('Set-Cookie')
            if cl:
                msg = 'Received cookies from: %s' % response + os.linesep
                msg += os.linesep.join('Set-Cookie: %s' % c for c in cl)
                log.msg(msg, level=log.DEBUG)

    def _format_cookie(self, cookie):
        # build cookie string
        cookie_str = '%s=%s' % (cookie['name'], cookie['value'])

        if cookie.get('path', None):
            cookie_str += '; Path=%s' % cookie['path']
        if cookie.get('domain', None):
            cookie_str += '; Domain=%s' % cookie['domain']

        return cookie_str

    def _get_request_cookies(self, jar, request):
        if isinstance(request.cookies, dict):
            cookie_list = [{'name': k, 'value': v} for k, v in
                           request.cookies.iteritems()]
        else:
            cookie_list = request.cookies

        cookies = [self._format_cookie(x) for x in cookie_list]
        headers = {'Set-Cookie': cookies}
        response = Response(request.url, headers=headers)
        return jar.make_cookies(response, request)
