from crawlmi.commands.base import BaseCommand
from crawlmi.exceptions import UsageError
from crawlmi.http import Request
from crawlmi.utils.url import any_to_uri


class Command(BaseCommand):
    requires_project = False

    def syntax(self):
        return '[options] <url>'

    def short_desc(self):
        return 'Fetch a URL using the Crawlmi downloader.'

    def help(self):
        return (
            'Fetch a URL using the Crawlmi downloader and print its content '
            'to stdout. You may want to use --nolog to disable logging')

    def add_options(self, parser):
        BaseCommand.add_options(self, parser)
        parser.add_option('--headers', dest='headers', action='store_true', help='print response HTTP headers instead of body')

    def _print_headers(self, headers, prefix):
        for key, values in headers.items():
            for value in values:
                print '%s %s: %s' % (prefix, key, value)

    def _print_response(self, response, options):
        print
        if options.headers:
            print 'Sent headers:'
            self._print_headers(response.request.headers, '>')
            print
            print 'Received headers %s:' % response
            self._print_headers(response.headers, '<')
        else:
            print 'Received body:'
            print response.body
        print

    def handle(self, args, options):
        if len(args) != 1:
            raise UsageError()
        cb = lambda x: self._print_response(x, options)
        url = any_to_uri(args[0])
        request = Request(url, callback=cb)

        self.engine.download(request)
        self.process.start()
