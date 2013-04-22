from cStringIO import StringIO

from crawlmi import log
from crawlmi.core.engine import Engine
from crawlmi.core.project import Project
from crawlmi.core.signal_manager import SignalManager
from crawlmi.settings import EngineSettings
from crawlmi.spider import BaseSpider
from crawlmi.stats import MemoryStats
from crawlmi.utils.clock import Clock


def get_engine(custom_settings=None, **kwargs):
    '''Return the engine initialized with the custom settings.
    '''
    custom_settings = custom_settings or {}
    custom_settings.update(kwargs)
    settings = EngineSettings(custom_settings=custom_settings)
    engine = Engine(settings, Project(path=None), clock=Clock())
    engine.set_spider(BaseSpider('dummy'))
    engine.close_if_idle = False
    # it is common to use stats and signals in unittests, without full
    # initialization of the engine
    engine.stats = MemoryStats(engine)
    engine.signals = SignalManager(engine)
    return engine


class LogWrapper(object):
    def setUp(self, level=log.INFO, encoding='utf-8'):
        self.f = StringIO()
        self.flo = log.CrawlmiFileLogObserver(self.f, level, encoding)
        self.flo.start()

    def tearDown(self):
        self.flo.stop()

    def clear(self):
        self.f.reset()
        self.f.truncate()

    def get_logged(self, clear=True):
        logged = self.f.getvalue()
        if clear:
            self.clear()
        return logged

    def get_lines(self, strip=True, clear=True):
        lines = self.get_logged(clear=clear).splitlines()
        if strip:
            lines = map(lambda l: l.strip()[25:], lines)
        return lines

    def get_first_line(self, strip=True, clear=True):
        lines = self.get_lines(strip=strip, clear=clear)
        return lines[0] if lines else ''
