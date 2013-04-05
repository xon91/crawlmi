from crawlmi.spider import BaseSpider


class Spider1(BaseSpider):
    name = 'spider1'
    allowed_domains = ['crawlmi1.org', 'crawlmi3.org']
