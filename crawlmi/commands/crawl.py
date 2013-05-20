from crawlmi.commands.base import BaseCommand
from crawlmi.exceptions import UsageError


class Command(BaseCommand):
    requires_project = True

    def syntax(self):
        return '[options] <spider>'

    def short_desc(self):
        return 'Start the crawling process of the spider.'

    def add_options(self, parser):
        BaseCommand.add_options(self, parser)
        parser.remove_option('--spider')  # spider is set through argument
        parser.add_option('-a', dest='spargs', action='append', default=[],
            metavar='NAME=VALUE', help='set spider argument (may be repeated)')

    def get_spider(self, engine, args, options):
        if len(args) != 1:
            raise UsageError()
        return engine.spiders.create_spider_by_name(args[0])

    def run(self, args, options):
        self.engine.crawl_start_requests()
        self.process.start()
