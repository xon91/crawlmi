from twisted.python.failure import Failure

from crawlmi.exceptions import RestartPipeline, RequestDropped
from crawlmi.http import Request, Response
from crawlmi.middleware.middleware_manager import MiddlewareManager
from crawlmi.utils.conf import build_component_list


def passthru(arg):
    return arg


class PipelineManager(MiddlewareManager):
    component_name = 'downloader pipeline'

    def __init__(self, *args, **kwargs):
        super(PipelineManager, self).__init__(*args, **kwargs)
        self._process_request = []
        self._process_response = []

        for mw in self.middlewares:
            name = mw.__class__.__name__
            self._process_request.append((
                name,
                getattr(mw, 'process_request', passthru)))
            self._process_response.append((
                name,
                getattr(mw, 'process_response', passthru),
                getattr(mw, 'process_failure', passthru)))
        self._process_response.reverse()

    def _get_mwlist(self):
        return build_component_list(self.settings['PIPELINE_BASE'],
                                    self.settings['PIPELINE'])

    def process_request(self, request):
        while True:
            try:
                for name, method in self._process_request:
                    request = method(request)
                    assert request is None or isinstance(request, (Request, Response)), \
                        'Middleware %s.process_request must return None, Response or Request, got %s' % \
                        (method.im_self.__class__.__name__, type(request))
                    if request is None:
                        raise RequestDropped(
                            '`%s` pipeline middleware dropped the request in `process_request()` method' %
                            name)
                    elif isinstance(request, Response):
                        return request
            except RestartPipeline as e:
                request = e.new_value
                assert isinstance(request, Request), \
                    'Middleware %s.process_request must raise RestartPipeline with Request, got %s' % \
                    (method.im_self.__class__.__name__, type(request))
            else:
                return request

    def process_response(self, response):
        # we can be sure that response.request is set from the downloader
        request = response.request

        for name, pr, pf in self._process_response:
            method = pr if isinstance(response, Response) else pf
            try:
                response = method(response)
            except:
                response = Failure()
            assert response is None or isinstance(response, (Request, Response, Failure)), \
                'Middleware %s.process_request must return None, Response, Request or Failure, got %s' % \
                (method.im_self.__class__.__name__, type(response))
            if response is None:
                method_name = 'process_response()' if method is pr else 'process_failure()'
                failure = Failure(RequestDropped(
                    '`%s` pipeline middleware dropped the request in `%s` method' %
                    (name, method_name)))
                failure.request = request
                return failure
            if not isinstance(response, (Response, Failure)):
                return response

            # make sure, request attribute is always set
            response.request = request
        return response
