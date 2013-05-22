from crawlmi import log
from crawlmi.utils.misc import iter_submodules
from crawlmi.utils.spider import iter_spider_classes
from crawlmi.utils.url import is_url_from_any_domain


class SpiderManager(object):
    '''SpiderManager provides an easy way to lookup and create available
    spiders inside the project.
    '''

    def __init__(self, settings):
        self.spider_modules = settings.get_list('SPIDER_MODULES')
        self._spiders = {}
        for path in self.spider_modules:
            for module in iter_submodules(path):
                self._load_spiders(module)

    def _load_spiders(self, module):
        for spider_class in iter_spider_classes(module):
            self._spiders[spider_class.name] = spider_class

    def get_spiders(self):
        '''Return the names of all the available spiders.
        '''
        return self._spiders.keys()

    def get_spiders_by_url(self, url):
        '''Return the names of all the available spiders that are prefered to
        handle the given url.
        '''
        spiders = []
        for name, cls in self._spiders.iteritems():
            allowed_domains = [name] + getattr(cls, 'allowed_domains', [])
            if is_url_from_any_domain(url, allowed_domains):
                spiders.append(name)
        return spiders

    def create_spider_by_name(self, name, spargs={}):
        spider_class = self._spiders.get(name)
        if spider_class is None:
            raise KeyError('Spider not found: %s' % name)
        return spider_class(**spargs)

    def create_spider_by_url(self, url, default_spider=None, spargs={}):
        spiders = self.get_spiders_by_url(url)

        if len(spiders) == 1:
            return self.create_spider_by_name(spiders[0])
        elif len(spiders) > 1:
            log.msg(
                format='More than one spider can handle: %(url)s - %(snames)s',
                level=log.ERROR, url=url, snames=', '.join(spiders))
        elif len(spiders) == 0:
            log.msg(
                format='Unable to find spider that handles: %(url)s',
                level=log.ERROR, url=url)
        return default_spider
