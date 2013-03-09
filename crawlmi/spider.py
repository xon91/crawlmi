class BaseSpider(object):
    name = None
    settings = {}  # spider-specific settings to override the default ones

    def __init__(self, name=None):
        self.name = name

    def start_requests(self):
        pass

    def set_engine(self, engine):
        self.engine = engine
        # overwrite spider-specific settings with the global settings
        self.settings = self.engine.settings

    def init_crawl(self):
        pass

    def resume_crawl(self):
        pass

    def parse(self, response):
        pass
