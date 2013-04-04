import signal

from twisted.internet import reactor

from crawlmi import log, signals
from crawlmi.utils.ossignal import install_shutdown_handlers, signal_names


class Process(object):
    '''Process is a wrapper around the engine. It starts the reactor and
    catches kill signals from OS.
    '''

    def __init__(self, engine):
        self.engine = engine

    def start(self):
        self.engine.signals.connect(self.stop, signal=signals.engine_stopped)
        self.engine.start()
        install_shutdown_handlers(self._signal_shutdown)
        reactor.addSystemEventTrigger('before', 'shutdown', self.stop)
        reactor.run(installSignalHandlers=False)  # blocking call

    def stop(self):
        if self.engine.running:
            self.engine.stop()
        self._stop_reactor()

    def _stop_reactor(self):
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
