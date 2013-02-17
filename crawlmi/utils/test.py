from crawlmi.core.engine import Engine
from crawlmi.settings import Settings
from crawlmi.spider import BaseSpider


def get_engine(custom_settings=None, **kwargs):
    custom_settings = Settings(custom_settings or {})
    custom_settings.update(kwargs)
    return Engine(BaseSpider('dummy'), custom_settings=custom_settings)
