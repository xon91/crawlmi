import datetime

from crawlmi import signals


class CoreStats(object):
    '''CoreStats collects stats like items scraped and start/finish times.
    '''

    def __init__(self, engine):
        self.stats = engine.stats
        engine.signals.connect(self.engine_started,
                               signal=signals.engine_started)
        engine.signals.connect(self.engine_stopped,
                               signal=signals.engine_stopped)
        engine.signals.connect(self.spider_error,
                               signal=signals.spider_error)

    def engine_started(self):
        self.time_start = datetime.datetime.utcnow()
        self.stats.set_value('time_start', self.time_start.isoformat())

    def engine_stopped(self, reason):
        self.time_finish = datetime.datetime.utcnow()
        self.stats.set_value('time_finish', self.time_finish.isoformat())

        time_total = self.time_finish - self.time_start
        self.stats.set_value('time_total', '%d days, %d seconds' %
                             (time_total.days, time_total.seconds))
        self.stats.set_value('finish_reason', reason)

    def spider_error(self, failure):
        self.stats.inc_value('spider_errors_count')
