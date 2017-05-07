from pydispatch import dispatcher
from twisted.internet import reactor, defer
from twisted.python import log as txlog
from twisted.python.failure import Failure
from twisted.trial import unittest

from crawlmi import log
from crawlmi.core.signal_manager import SignalManager


test_signal = object()


class SignalManagerTest(unittest.TestCase):
    def setUp(self):
        self.handlers_called = set()
        txlog.addObserver(self._log_received)
        self.manager = SignalManager()

    def tearDown(self):
        txlog.removeObserver(self._log_received)
        self.flushLoggedErrors()

    def _log_received(self, event):
        self.handlers_called.add(self._log_received)
        self.assertIn('error_handler', event['message'][0])
        self.assertEqual(event['logLevel'], log.ERROR)

    def _error_handler(self, arg):
        self.handlers_called.add(self._error_handler)
        a = 1 / 0

    def _ok_handler(self, arg):
        self.handlers_called.add(self._ok_handler)
        self.assertEqual(arg, 'test')
        return 'OK'

    def _test(self, ok_handler, error_handler, get_result):
        dispatcher.connect(error_handler, signal=test_signal)
        dispatcher.connect(ok_handler, signal=test_signal)
        result = yield defer.maybeDeferred(get_result, test_signal, arg='test')

        self.assertIn(error_handler, self.handlers_called)
        self.assertIn(ok_handler, self.handlers_called)
        self.assertIn(self._log_received, self.handlers_called)
        self.assertEqual(result[0][0], error_handler)
        self.assertIsInstance(result[0][1], Failure)
        self.assertEqual(result[1], (self.ok_handler, 'OK'))

        dispatcher.disconnect(error_handler, signal=test_signal)
        dispatcher.disconnect(ok_handler, signal=test_signal)

    def test_send(self):
        self._test(self._ok_handler, self._error_handler, self.manager.send)

    def test_send_deferred(self):
        self._test(self._ok_handler, self._error_handler, self.manager.send_deferred)

    def test_send_deffered2(self):
        def ok_handler(arg):
            self.handlers_called.add(ok_handler)
            self.assertEqual(arg, 'test')
            d = defer.Deferred()
            reactor.callLater(0, d.callback, 'OK')
            return d
        self._test(ok_handler, self._error_handler, self.manager.send_deferred)

    def test_error_logged_if_deferred_not_supported(self):
        test_handler = lambda: defer.Deferred()
        log_events = []
        txlog.addObserver(log_events.append)
        dispatcher.connect(test_handler, test_signal)
        self.manager.send(test_signal)
        self.failUnless(log_events)
        self.failUnless('Cannot return deferreds from signal handler' in str(log_events))
        txlog.removeObserver(log_events.append)
        dispatcher.disconnect(test_handler, test_signal)
