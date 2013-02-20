from twisted.python.failure import Failure

from crawlmi.exceptions import RestartPipeline
from crawlmi.http.request import Request
from crawlmi.http.response import Response
from crawlmi.middleware.middleware_manager import MiddlewareManager
from crawlmi.utils.conf import build_component_list


class PipelineManager(MiddlewareManager):
    component_name = 'downloader pipeline'

    def __init__(self, *args, **kwargs):
        super(PipelineManager, self).__init__(*args, **kwargs)
        self._process_request = []
        self._process_response = []

        for mw in self.middlewares:
            self._process_request.append(
                getattr(mw, 'process_request', lambda x: x))
            self._process_response.append((
                getattr(mw, 'process_response', lambda x: x),
                getattr(mw, 'process_failure', lambda x: x)))
        self._process_response.reverse()

    def _get_mwlist(self):
        return build_component_list(self.settings['PIPELINE_BASE'],
                                    self.settings['PIPELINE'])

    def process_request(self, request):
        while True:
            try:
                for method in self._process_request:
                    request = method(request)
                    assert request is None or isinstance(request, (Request, Response)), \
                        'Middleware %s.process_request must return None, Response or Request, got %s' % \
                        (method.im_self.__class__.__name__, type(request))
                    if not isinstance(request, Request):
                        return request
            except RestartPipeline as e:
                request = e.new_value
                assert isinstance(request, Request), \
                    'Middleware %s.process_request must raise RestartPipeline with Request, got %s' % \
                    (method.im_self.__class__.__name__, type(request))
            else:
                return request

    def process_response(self, response):
        request = response.request

        for pr, pf in self._process_response:
            method = pr if isinstance(response, Response) else pf
            try:
                response = method(response)
            except:
                response = Failure()
            assert response is None or isinstance(response, (Request, Response, Failure)), \
                'Middleware %s.process_request must return None, Response, Request or Failure, got %s' % \
                (method.im_self.__class__.__name__, type(response))
            if not isinstance(response, (Response, Failure)):
                return response

            # make sure, request parameter is always set
            response.request = request
        return response
