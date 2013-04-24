from crawlmi.utils.trackref import object_ref


class BaseSpider(object_ref):
    name = None

    def __init__(self, name=None):
        if name is not None:
            self.name = name

    @classmethod
    def spider_settings(cls):
        return {}

    def start_requests(self):
        pass

    def set_engine(self, engine):
        self.engine = engine
        self.settings = self.engine.settings

    def parse(self, response):
        pass

    def __str__(self):
        return '<%s %r at 0x%0x>' % (type(self).__name__, self.name, id(self))
    __repr__ = __str__
