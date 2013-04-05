from crawlmi.commands.base import BaseCommand
from crawlmi.exceptions import UsageError
from crawlmi.http.request import Request
from crawlmi.utils.response import open_in_browser
from crawlmi.utils.url import any_to_uri


class Command(BaseCommand):
    requires_project = False

    def syntax(self):
        return '[options] <url>'

    def short_desc(self):
        return 'Open URL in browser, as seen by Crawlmi.'

    def help(self):
        return (
            'Fetch a URL using the Crawlmi downloader and show its '
            'contents in a browser')

    def handle(self, args, options):
        if len(args) != 1:
            raise UsageError()
        url = any_to_uri(args[0])
        request = Request(url, callback=open_in_browser)

        self.engine.download(request)
        self.process.start()
