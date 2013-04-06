from time import time

from twisted.internet import reactor
from twisted.python.failure import Failure

from crawlmi import log, signals
from crawlmi.core.downloader import Downloader
from crawlmi.core.signal_manager import SignalManager
from crawlmi.http import Request, Response
from crawlmi.middleware.extension_manager import ExtensionManager
from crawlmi.middleware.pipeline_manager import PipelineManager
from crawlmi.queue import PriorityQueue, MemoryQueue
from crawlmi.spider.spider_manager import SpiderManager
from crawlmi.utils.defer import LoopingCall, defer_result
from crawlmi.utils.misc import arg_to_iter, load_object


class Engine(object):
    '''
    WARNING: don't stop() and start() engine. Use pause() and unpause(),
    instead.
    '''

    # how many seconds to wait between the checks of outq
    QUEUE_CHECK_FREQUENCY = 0.1

    def __init__(self, settings, project, clock=None):
        '''Constructor of Engine should be very lightweight, so that things
        can be easily unittested. For any more complicated initialization
        use `setup()`.
        '''
        self.settings = settings
        self.project = project
        self.spiders = SpiderManager(settings)

        self.close_if_idle = True
        self.initialized = False  # True, when `setup()` has been called

        self.spider = None
        self.pending_requests = 0
        self.running = False
        self.paused = False
        # clock is used in unittests
        self.clock = clock or reactor
        self.processing = LoopingCall(self._process_queue, clock=self.clock)

    def set_spider(self, spider):
        self.spider = spider
        self.settings.spider_settings = spider.spider_settings

    def setup(self):
        assert self.spider is not None, 'Spider is not set in Engine.'

        # IMPORTANT: order of the following initializations is very important
        # so please, think twice about any changes to it

        # initialize logging
        if self.settings.get_bool('LOG_ENABLED'):
            log.start(
                self.settings['LOG_FILE'],
                self.settings['LOG_LEVEL'],
                self.settings['LOG_STDOUT'],
                self.settings['LOG_ENCODING'])

        # initialize signals
        self.signals = SignalManager(self)

        #initialize stats
        stats_cls = load_object(self.settings.get('STATS_CLASS'))
        self.stats = stats_cls(self)

        # initialize downloader
        self.inq = PriorityQueue(lambda _: MemoryQueue())
        self.outq = MemoryQueue()
        self.downloader = Downloader(self.settings, self.inq, self.outq,
                                     clock=self.clock)

        # initialize extensions
        self.extensions = ExtensionManager(self)
        # initialize downloader pipeline
        self.pipeline = PipelineManager(self)

        self.initialized = True

        # now that everything is ready, set the spider's engine
        self.spider.set_engine(self)

    def start(self):
        assert self.initialized, 'Engine is not initialized. Call `setup()` to initialize it.'

        self.start_time = time()
        self.running = True
        self.signals.send(signal=signals.engine_started)
        self.processing.schedule(self.QUEUE_CHECK_FREQUENCY)

        # process start requests from spider
        try:
            requests = self.spider.start_requests()
            for req in arg_to_iter(requests):
                self.download(req)
        except:
            log.err(Failure(), 'Error when processing start requests.')

    def stop(self, reason=''):
        assert self.running, 'Engine is not running. Why stopping it?'

        self.signals.send(signal=signals.engine_stopping, reason=reason)
        self.running = False
        self.processing.cancel()
        self.downloader.close()
        self.inq.close()
        self.outq.close()
        log.msg(format='Engine stopped (%(reason)s)', reason=reason)
        self.signals.send(signal=signals.engine_stopped, reason=reason)
        self.stats.dump_stats()

    def pause(self):
        self.paused = True
        self.processing.schedule(5)

    def unpause(self):
        self.paused = False
        self.processing.schedule(self.QUEUE_CHECK_FREQUENCY)

    def download(self, request):
        '''"Download" the given request. First pass it through the downloader
        pipeline.
            - if the request is received from the pipeline, push it to inq
            - if the response is received from the pipeline, push it to outq
        '''
        request_or_response = self.pipeline.process_request(request)
        if request_or_response is None:
            return

        if isinstance(request_or_response, Request):
            self.pending_requests += 1
            self.signals.send(signal=signals.request_received,
                              request=request_or_response)
            self.inq.push(request_or_response.priority, request_or_response)
        elif isinstance(request_or_response, Response):
            request_or_response.request = request
            self.outq.push(request_or_response)

    def is_idle(self):
        return self.pending_requests == 0 and len(self.outq) == 0

    def _process_queue(self):
        while self.running and not self.paused and self.outq:
            response = self.outq.pop()
            self.signals.send(signal=signals.response_downloaded,
                              response=response)
            dfd = defer_result(response, clock=self.clock)
            dfd.addBoth(self.pipeline.process_response)
            dfd.addBoth(self._handle_pipeline_result)
            dfd.addBoth(self._finalize_download)

        # check stopping condition
        if self.close_if_idle and self.is_idle():
            self.stop('finished')

    def _finalize_download(self, _):
        self.pending_requests -= 1

    def _handle_pipeline_result(self, result):
        if result is None:
            pass
        elif isinstance(result, Request):
            self.download(result)
        else:
            request = result.request
            self.signals.send(signal=signals.response_received,
                              response=result)
            dfd = defer_result(result, clock=self.clock)
            dfd.addCallbacks(request.callback or self.spider.parse,
                             request.errback)
            dfd.addCallbacks(
                self._handle_spider_output,
                self._handle_spider_error,
                callbackKeywords={'request': request},
                errbackKeywords={'request': request})
            return dfd

    def _handle_spider_output(self, result, request):
        result = arg_to_iter(result)
        for request in result:
            assert isinstance(request, Request), \
                'spider must return None, request or iterable of requests'
            self.download(request)

    def _handle_spider_error(self, failure, request):
        # set `request` in a case the error was raised inside the spider
        failure.request = request
        self.signals.send(signal=signals.spider_error, failure=failure)
        log.err(failure, 'Error when downloading %s' % request)

    def __str__(self):
        return '<%s at 0x%0x>' % (type(self).__name__, id(self))
    __repr__ = __str__
