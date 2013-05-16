from . import BaseSpider
from crawlmi import log, signals
from crawlmi.http import Request
from crawlmi.utils.python import regex
from crawlmi.utils.sitemap import (get_sitemap_body, iter_urls_from_robots,
                                   get_sitemap_type, iter_urls_from_sitemap)


class SitemapSpider(BaseSpider):
    '''SitemapSpider is an abstract spider for scraping the sites from their
    sitemaps. It can deal with <sitemapindex> and <urlset> sitemaps and
    robots.txt files.

    For <sitemapindex> it follows all the links matching any of the
    `sitemap_follow` patterns.
    For <urlset> it follows all the links matching any of the `sitemap_rules`
    patterns. In a case of match, it uses the first match as the callback
    function.
    From robots.txt files sitemap urls are extracted and are treated the same
    way as if they were from <sitemapindex> sitemaps.

    !Important! Sitemaps are downloaded one at a time. The next
    sitemap is downloaded when all the requests have been processed from the
    previous sitemap.
    '''

    # list of sitemap urls where to start crawling. Can also point to
    # robots.txt files.
    sitemap_urls = []
    # list of (regexp, function) pairs. If regexp matches the url, the
    # function from the pair is called.
    sitemap_rules = [('', 'parse')]
    # list of regexps. Used when sitemap is of type <sitemapindex>.
    # If regexp matches the the url, the url is followed.
    sitemap_follow = ['']

    def __init__(self, *a, **kw):
        super(SitemapSpider, self).__init__(*a, **kw)
        self._cbs = []
        for rule, cb in self.sitemap_rules:
            if isinstance(cb, basestring):
                cb = getattr(self, cb)
            self._cbs.append((regex(rule), cb))
        self._follow = [regex(x) for x in self.sitemap_follow]
        self._current_sitemap_url = None
        self._sitemap_urls = self.sitemap_urls[:]
        self._site_urls = []

    def set_engine(self, engine):
        super(SitemapSpider, self).set_engine(engine)
        self._batch_size = 3 * engine.downloader.total_concurrency
        if engine.command_invoked == 'crawl':
            self.engine.signals.connect(self._spider_idle,
                                        signal=signals.spider_idle)

    def _spider_idle(self):
        # schedule site requests
        current_batch = 0
        while current_batch < self._batch_size and self._site_urls:
            url = self._site_urls.pop()
            req = self._process_site_url(url)
            if req:
                current_batch += 1
                self.engine.download(req)
        if current_batch:
            return

        # sitemap finished
        if self._current_sitemap_url is not None:
            self.sitemap_finished(self._current_sitemap_url)
            self.engine.stats.inc_value('sitemaps_processed')

        # schedule sitemap request
        while self._sitemap_urls:
            url = self._sitemap_urls.pop()
            req = self._process_sitemap_url(url)
            if req:
                self._current_sitemap_url = req.url
                self.engine.download(req)
                return

    def start_requests(self):
        '''Do not override this! Fill `sitemap_urls`, instead.
        The intention is to download one sitemap at a time. SitemapSpider
        uses `spider_idle` signals, so everytime SitemapSpider goes idle,
        new sitemap is downloaded.
        '''
        return []

    def process_sitemap_request(self, request):
        '''Override this method to do additional work on sitemap request
        before it is downloaded.
        If None is returned, the request is skipped.
        '''
        return request

    def process_site_request(self, request):
        '''Override this method to do additional work on a request parsed
        from urlset sitemap.
        If None is returned, the request is skipped.
        '''
        return request

    def sitemap_finished(self, sitemap_url):
        '''This method is called, when all the links from the sitemap are downloaded.
        Override it to do some finalization work.
        '''
        pass

    def _parse_sitemap(self, response):
        requests = []

        if response.url.endswith('/robots.txt'):
            self._sitemap_urls.extend(iter_urls_from_robots(response.body))
        else:
            sitemap_body = get_sitemap_body(response)
            if sitemap_body is None:
                log.msg(format='Invalid sitemap %(url)s',
                        level=log.WARNING, url=response.url)
                return []

            sitemap_type = get_sitemap_type(sitemap_body)
            if sitemap_type == 'sitemapindex':
                log.msg(format='Sitemap %(url)s is of type <sitemapindex>',
                        level=log.DEBUG, url=response.url)
                self._sitemap_urls.extend(iter_urls_from_sitemap(sitemap_body))
            elif sitemap_type == 'urlset':
                log.msg(format='Sitemap %(url)s is of type <urlset>',
                        level=log.DEBUG, url=response.url)
                self._site_urls.extend(iter_urls_from_sitemap(sitemap_body))
            else:
                log.msg(format='Unrecognized type of sitemap %(url)s: %(stype)s',
                        level=log.WARNING, url=response.url, stype=sitemap_type)
        return requests

    def _process_sitemap_url(self, url):
        if url in self.sitemap_urls or any(x.search(url) for x in self._follow):
            req = Request(url, callback=self._parse_sitemap)
            return self.process_sitemap_request(req)

    def _process_site_url(self, url):
        for rule, cb in self._cbs:
            if rule.search(url):
                req = Request(url, callback=cb)
                return self.process_site_request(req)
