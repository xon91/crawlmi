from twisted.python.failure import Failure

from crawlmi.exceptions import RestartPipeline, DropRequest
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
                mw.enabled_setting,
                getattr(mw, 'process_request', passthru)))
            self._process_response.append((
                name,
                mw.enabled_setting,
                getattr(mw, 'process_response', passthru),
                getattr(mw, 'process_failure', passthru)))
        self._process_response.reverse()

    def _get_mwlist(self):
        return build_component_list(self.settings['PIPELINE_BASE'],
                                    self.settings['PIPELINE'])

    def process_request(self, request):
        '''Passes request through the pipeline middlewares.
        It automatically restarts the processing when RestartPipeline is
        raised.

        Return value is either Request or Response object or the exception
        DropRequest is raised.
        '''
        while True:
            try:
                for name, enabled_setting, method in self._process_request:
                    # skip disabled mw through meta
                    if not request.meta.get(enabled_setting, True):
                        continue
                    request = method(request)
                    assert request is None or isinstance(request, (Request, Response)), \
                        'Middleware %s.process_request must return None, Response or Request, got %s' % \
                        (method.im_self.__class__.__name__, type(request))
                    if request is None:
                        raise DropRequest(
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
        '''Passes response (Response or Failure object) received from
        Downloader thought pipeline middlewares.

        Return value is either Request, Response or Failure object.
        '''
        # we can be sure that response.request is set from the downloader
        request = response.request

        for name, enabled_setting, pr, pf in self._process_response:
            # skip disabled mw through meta
            if not request.meta.get(enabled_setting, True):
                continue
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
                failure = Failure(DropRequest(
                    '`%s` pipeline middleware dropped the request in `%s` method' %
                    (name, method_name)))
                failure.request = request
                return failure
            if not isinstance(response, (Response, Failure)):
                return response

            # make sure, request attribute is always set
            response.request = request
        return response
