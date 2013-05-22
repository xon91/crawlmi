from crawlmi.spider import BaseSpider


class Spider2(BaseSpider):
    name = 'spider2'
    allowed_domains = ['crawlmi2.org', 'crawlmi3.org']

    def __init__(self, p1, p2, *args, **kwargs):
        super(Spider2, self).__init__(*args, **kwargs)
        self.p1 = p1
        self.p2 = p2
