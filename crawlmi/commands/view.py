from crawlmi.commands.base import BaseCommand
from crawlmi.exceptions import UsageError
from crawlmi.http.request import Request
from crawlmi.utils.response import open_in_browser
from crawlmi.utils.url import is_url


class Command(BaseCommand):
    requires_project = False

    def syntax(self):
        return '[options] <url>'

    def short_desc(self):
        return 'Open URL in browser, as seen by Scrapy.'

    def help(self):
        return (
            'Fetch a URL using the Scrapy downloader and show its '
            'contents in a browser')

    def handle(self, args, options):
        if len(args) != 1 or not is_url(args[0]):
            raise UsageError()
        request = Request(args[0], callback=open_in_browser)

        self.engine.download(request)
        self.process.start()
