import signal

from twisted.internet import reactor, defer

from crawlmi import log, signals
from crawlmi.utils.ossignal import install_shutdown_handlers, signal_names


class Process(object):
    '''Process is a wrapper around the engine. It starts the reactor and
    catches kill signals from OS.
    '''

    def __init__(self, engine):
        self.engine = engine
        install_shutdown_handlers(self._signal_shutdown)

    def start(self):
        assert self.engine.initialized, 'Engine was not initialzied. Call `setup()` to initialize it.'
        self.engine.signals.connect(self.stop, signal=signals.engine_stopped)
        self.engine.start()
        reactor.addSystemEventTrigger('before', 'shutdown', self.stop)
        reactor.run(installSignalHandlers=False)  # blocking call

    def stop(self):
        if self.engine.running:
            dfd = self.engine.stop()
        else:
            dfd = defer.succeed(None)
        dfd.addBoth(self._stop_reactor)

    def _stop_reactor(self, _=None):
        try:
            reactor.stop()
        except RuntimeError:  # raised if already stopped or in shutdown stage
            pass

    def _signal_shutdown(self, signum, _):
        install_shutdown_handlers(self._signal_kill)
        signame = signal_names[signum]
        log.msg(format='Received %(signame)s, shutting down gracefully. Send again to force.',
                level=log.INFO, signame=signame)
        reactor.callFromThread(self.stop)

    def _signal_kill(self, signum, _):
        install_shutdown_handlers(signal.SIG_IGN)
        signame = signal_names[signum]
        log.msg(format='Received %(signame)s twice, forcing unclean shutdown.',
                level=log.INFO, signame=signame)
        reactor.callFromThread(self._stop_reactor)
