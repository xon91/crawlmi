from twisted.python.failure import Failure
from twisted.trial import unittest

from crawlmi import signals
from crawlmi.core.engine import Engine
from crawlmi.core.signal_manager import SignalManager
from crawlmi.exceptions import DontStopEngine, StopEngine
from crawlmi.http import Request, Response
from crawlmi.middleware.extension_manager import ExtensionManager
from crawlmi.middleware.pipeline_manager import PipelineManager
from crawlmi.queue import PriorityQueue, MemoryQueue
from crawlmi.settings import EngineSettings
from crawlmi.spider import BaseSpider
from crawlmi.stats import MemoryStats
from crawlmi.utils.test import get_engine


class SignalProcessor(object):
    active_signals = [
        signals.engine_started,
        signals.engine_stopping,
        signals.engine_stopped,
        signals.request_received,
        signals.response_downloaded,
        signals.response_received,
        signals.failure_received,
        signals.spider_error,
        signals.spider_idle,
    ]

    def __init__(self, engine):
        self.received = []
        for signal in self.active_signals:
            proc = self._get_proc(signal)
            # we need to keep strong reference
            self.__dict__[str(signal)] = proc
            engine.signals.connect(proc, signal=signal)

    def _get_proc(self, signal):
        def proc():
            self.received.append(signal)
        return proc


class Pipeline(object):
    def __init__(self, engine):
        self.req = None
        self.resp = None
        self.fail = None
        Pipeline.obj = self

    def process_request(self, request):
        return self.req(request) if self.req else request

    def process_response(self, response):
        return self.resp(response) if self.resp else response

    def process_failure(self, failure):
        return self.fail(failure) if self.fail else failure


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.engine = get_engine(
            LOG_ENABLED=False,
            PIPELINE_BASE={'crawlmi.tests.test_engine.Pipeline': 10})
        self.clock = self.engine.clock
        self.engine.setup()
        self.sp = SignalProcessor(self.engine)
        self.pipeline = Pipeline.obj

    def tearDown(self):
        if self.engine.running:
            self.engine.stop('finished')
        self.flushLoggedErrors()

    def test_init(self):
        self.assertIsInstance(self.engine.spider, BaseSpider)
        self.assertIsInstance(self.engine.settings, EngineSettings)
        self.assertFalse(self.engine.running)
        self.assertFalse(self.engine.paused)
        self.assertIsInstance(self.engine.signals, SignalManager)
        self.assertIsInstance(self.engine.stats, MemoryStats)
        self.assertIsInstance(self.engine.request_queue, PriorityQueue)
        self.assertEqual(len(self.engine.request_queue), 0)
        self.assertIsInstance(self.engine.response_queue, MemoryQueue)
        self.assertEqual(len(self.engine.response_queue), 0)
        self.assertIsInstance(self.engine.extensions, ExtensionManager)
        self.assertIsInstance(self.engine.pipeline, PipelineManager)
        self.assertEqual(self.engine.spider.engine, self.engine)

    def check_signals(self, signals=None):
        if signals is not None:
            self.assertEqual(len(self.sp.received), len(signals), str(self.sp.received))
            for i in xrange(len(signals)):
                self.assertEqual(self.sp.received[i], signals[i])
        del self.sp.received[:]

    def test_start_stop(self):
        self.engine.start()
        self.check_signals([signals.engine_started])
        self.engine.stop('finished')
        self.check_signals([signals.engine_stopping, signals.engine_stopped])
        self.assertFalse(self.engine.running)
        self.assertTrue(self.engine.request_queue._closed)
        self.assertTrue(self.engine.response_queue._closed)

    def test_download(self):
        self.engine.start()
        del self.sp.received[:]

        req = Request('http://github.com/')
        self.engine.download(req)
        self.clock.advance(0)
        self.check_signals([signals.request_received])
        self.assertEqual(len(self.engine.request_queue), 1)

        # pipeline None
        self.pipeline.req = lambda req: None
        self.engine.download(req)
        self.clock.advance(0)
        self.assertEqual(len(self.engine.request_queue), 1)

        # pipeline response
        self.pipeline.req = lambda req: Response('')
        self.engine.download(req)
        self.clock.advance(0)
        self.assertEqual(len(self.engine.response_queue), 1)

        # download and stop
        self.pipeline.req = lambda req: Response('')
        d = self.engine.download(req)
        self.engine.stop('finished')
        self.clock.advance(0)
        return d

    def test_processing(self):
        self.engine.start()
        del self.sp.received[:]

        # normal behavior
        req = Request('http://github.com/')
        resp = Response('', request=req)
        self.engine.response_queue.push(resp)
        self.clock.pump([self.engine.QUEUE_CHECK_FREQUENCY, 0])
        self.check_signals([signals.response_downloaded,
                            signals.response_received])

        # download error
        fail = Failure(Exception())
        fail.request = req
        self.engine.response_queue.push(fail)
        self.clock.pump([self.engine.QUEUE_CHECK_FREQUENCY, 0, 0, 0])
        self.check_signals([signals.failure_received,
                            signals.spider_error])

        # pipeline None
        self.pipeline.resp = lambda req: None
        self.engine.response_queue.push(resp)
        self.clock.pump([self.engine.QUEUE_CHECK_FREQUENCY, 0, 0])
        self.check_signals([signals.response_downloaded,
                            signals.failure_received,
                            signals.spider_error])

        # pipeline request
        self.pipeline.resp = lambda req: Request('http://github.com/')
        self.engine.response_queue.push(resp)
        self.clock.pump([self.engine.QUEUE_CHECK_FREQUENCY, 0, 0])
        self.check_signals([signals.response_downloaded,
                            signals.request_received])
        self.assertEqual(len(self.engine.request_queue), 1)
        self.engine.request_queue.pop()

        # pipeline failure
        self.pipeline.resp = lambda req: Failure(Exception())
        self.engine.response_queue.push(resp)
        self.clock.pump([self.engine.QUEUE_CHECK_FREQUENCY, 0, 0])
        self.check_signals([signals.response_downloaded,
                            signals.failure_received,
                            signals.spider_error])

    def test_idle(self):
        def _spider_idle_exception():
            raise DontStopEngine()

        def _spider_idle_schedule():
            self.engine.download(Request('http://github.com/'))

        self.engine.stop_if_idle = True
        self.engine.start()
        del self.sp.received[:]

        # don't stop, when DontStopEngine is raised
        self.engine.signals.connect(_spider_idle_exception, signal=signals.spider_idle)
        self.assertTrue(self.engine.is_idle())
        self.clock.advance(self.engine.QUEUE_CHECK_FREQUENCY)
        self.check_signals([signals.spider_idle])
        self.assertTrue(self.engine.running)
        self.engine.signals.disconnect(_spider_idle_exception, signal=signals.spider_idle)

        # don't stop when more requests are scheduled
        self.engine.signals.connect(_spider_idle_schedule, signal=signals.spider_idle)
        self.assertTrue(self.engine.is_idle())
        self.clock.advance(self.engine.IDLE_CHECK_FREQUENCY)
        self.check_signals([signals.spider_idle])
        self.assertFalse(self.engine.is_idle())
        self.assertTrue(self.engine.running)
        self.engine.signals.disconnect(_spider_idle_schedule, signal=signals.spider_idle)
        # clear scheduled request
        self.clock.advance(0)
        self.engine.request_queue.pop()
        self.engine.pending_requests = 0
        del self.sp.received[:]

        # don't stop when stop_if_idle is false
        self.engine.stop_if_idle = False
        self.assertTrue(self.engine.is_idle())
        self.clock.advance(Engine.IDLE_CHECK_FREQUENCY)
        self.check_signals([signals.spider_idle])
        self.assertTrue(self.engine.running)

        # now stop
        self.engine.stop_if_idle = True
        self.assertTrue(self.engine.is_idle())
        self.clock.advance(Engine.IDLE_CHECK_FREQUENCY)
        self.check_signals([signals.spider_idle,
                            signals.engine_stopping,
                            signals.engine_stopped])
        self.assertFalse(self.engine.running)

    def test_stop_engine(self):
        def _stop_engine(response):
            raise StopEngine()

        def _engine_stopping():
            self.assertEqual(len(self.engine.response_queue), 1)

        req1 = Request('http://github.com/', callback=_stop_engine)
        resp1 = Response('', request=req1)
        self.engine.response_queue.push(resp1)
        req2 = Request('http://github.com/')
        resp2 = Response('', request=req2)
        self.engine.response_queue.push(resp2)

        self.engine.signals.connect(_engine_stopping, signal=signals.engine_stopping)
        self.engine.start()
        self.assertTrue(self.engine.running)
        self.clock.pump([self.engine.QUEUE_CHECK_FREQUENCY, 0, 0])
        self.assertFalse(self.engine.running)
