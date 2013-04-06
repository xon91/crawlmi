from urlparse import urljoin

from crawlmi import log


class BaseRedirect(object):
    def __init__(self, engine):
        self.max_redirect_times = engine.settings.get_int('REDIRECT_MAX_TIMES')
        self.priority_adjust = engine.settings.get_int('REDIRECT_PRIORITY_ADJUST')

    def _redirect(self, redirected, request, reason):
        if len(redirected.history) < self.max_redirect_times:
            redirected.history.append(request.url)
            redirected.priority = request.priority + self.priority_adjust
            log.msg(format='Redirecting (%(reason)s) to %(redirected)s from %(request)s',
                    level=log.DEBUG, request=request,
                    redirected=redirected, reason=reason)
            return redirected
        else:
            log.msg(format='Discarding %(request)s: max redirections reached',
                    level=log.DEBUG, request=request)
            return None

    def _redirect_request_using_get(self, request, redirect_url):
        redirected = request.replace(url=redirect_url, method='GET', body='')
        redirected.headers.pop('Content-Type', None)
        redirected.headers.pop('Content-Length', None)
        return redirected


class Redirect(BaseRedirect):
    '''Handle redirection of requests based on response status and
    meta-refresh html tag.
    '''

    def process_response(self, response):
        request = response.request

        if request.method == 'HEAD':
            if response.status in [301, 302, 303, 307] and 'Location' in response.headers:
                redirected_url = urljoin(request.url, response.headers['location'])
                redirected = request.replace(url=redirected_url)
                return self._redirect(redirected, request, response.status)
            else:
                return response

        if response.status in [302, 303] and 'Location' in response.headers:
            redirected_url = urljoin(request.url, response.headers['location'])
            redirected = self._redirect_request_using_get(request, redirected_url)
            return self._redirect(redirected, request, response.status)

        if response.status in [301, 307] and 'Location' in response.headers:
            redirected_url = urljoin(request.url, response.headers['location'])
            redirected = request.replace(url=redirected_url)
            return self._redirect(redirected, request, response.status)

        return response
