from crawlmi import log, signals
from crawlmi.exceptions import NotConfigured
from crawlmi.utils.defer import LoopingCall


class LogStats(object):
    def __init__(self, engine, clock=None):
        self.interval = engine.settings.get_float('LOG_STATS_INTERVAL')
        if not self.interval:
            raise NotConfigured
        self.multiplier = 60.0 / self.interval
        self.logging = LoopingCall(self.log, clock=clock)

        engine.signals.connect(self.engine_started, signal=signals.engine_started)
        engine.signals.connect(self.engine_stopped, signal=signals.engine_stopped)
        engine.signals.connect(self.response_received, signal=signals.response_received)

        self.downloaded = 0
        self.downloaded_prev = 0

    def engine_started(self):
        self.logging.schedule(self.interval)

    def engine_stopped(self):
        self.logging.cancel()

    def response_received(self):
        self.downloaded += 1

    def log(self):
        per_minute = (self.downloaded - self.downloaded_prev) * self.multiplier
        self.downloaded_prev = self.downloaded
        msg = 'Crawled %d pages (at %d pages/min)' % (self.downloaded, per_minute)
        log.msg(msg)
