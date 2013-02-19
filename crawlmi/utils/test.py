from cStringIO import StringIO

from crawlmi import log
from crawlmi.core.engine import Engine
from crawlmi.settings import Settings
from crawlmi.spider import BaseSpider


def get_engine(custom_settings=None, **kwargs):
    '''Return the engine initialized with the custom settings.
    '''
    custom_settings = Settings(custom_settings or {})
    custom_settings.update(kwargs)
    return Engine(BaseSpider('dummy'), custom_settings=custom_settings)


class LogWrapper(object):
    def setUp(self, level, encoding):
        self.f = StringIO()
        self.flo = log.CrawlmiFileLogObserver(self.f, level, encoding)
        self.flo.start()

    def tearDown(self):
        self.flo.stop()

    def get_logged(self, strip=True):
        logged = self.f.getvalue()
        if strip:
            logged = logged.strip()[25:]
        return logged

    def get_first_line(self, strip=True):
        logged = self.get_logged(strip)
        return logged.splitlines()[0] if logged else ''
