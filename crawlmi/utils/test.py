from cStringIO import StringIO

from crawlmi import log
from crawlmi.core.engine import Engine
from crawlmi.settings import Settings
from crawlmi.spider import BaseSpider
from crawlmi.utils.clock import Clock


def get_engine(custom_settings=None, **kwargs):
    '''Return the engine initialized with the custom settings.
    '''
    settings = custom_settings or {}
    settings.update(kwargs)
    settings = Settings(settings)
    engine = Engine(BaseSpider('dummy'), custom_settings=settings,
                    clock=Clock())
    # disable stopping engine when idle
    engine.is_idle = lambda: False
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
