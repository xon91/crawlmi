from crawlmi.spider import BaseSpider


class Spider2(BaseSpider):
    name = 'spider2'
    allowed_domains = ['crawlmi2.org', 'crawlmi3.org']
