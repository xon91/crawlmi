import signal

from twisted.internet import reactor, threads

from crawlmi.http.request import Request
from crawlmi.http.response import Response
from crawlmi.parser.selectors import XPathSelector
from crawlmi.settings import Settings
from crawlmi.spider import BaseSpider
from crawlmi.utils.console import start_python_console
from crawlmi.utils.request import request_deferred
from crawlmi.utils.response import open_in_browser
from crawlmi.utils.url import any_to_uri


class Shell(object):
    relevant_classes = (BaseSpider, Request, Response, XPathSelector, Settings)

    def __init__(self, engine, update_vars=None):
        self.engine = engine
        self.engine.close_if_idle = False
        self.update_vars = update_vars or (lambda x: None)
        self.vars = {}
        # disable accidental Ctrl-C key press from shutting down the engine
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def start(self, url=None, request=None, response=None):
        if url:
            self.fetch(url)
        elif request:
            self.fetch(request)
        elif response:
            request = response.request
            self.populate_vars(request, response)
        else:
            self.populate_vars()
        start_python_console(self.vars)
        threads.blockingCallFromThread(reactor, self.engine.stop)

    def fetch(self, request_or_url):
        if isinstance(request_or_url, Request):
            request = request_or_url
            url = request.url
        else:
            url = any_to_uri(request_or_url)
            request = Request(url)
        response = threads.blockingCallFromThread(reactor, self._schedule, request)
        self.populate_vars(request, response)

    def _schedule(self, request):
        d = request_deferred(request)
        self.engine.download(request)
        return d

    def populate_vars(self, request=None, response=None):
        self.vars['settings'] = self.engine.settings
        self.vars['spider'] = self.engine.spider
        self.vars['request'] = request
        self.vars['response'] = response
        if hasattr(response, 'selector'):
            self.vars['xs'] = response.selector
        self.vars['fetch'] = self.fetch
        self.vars['view'] = open_in_browser
        self.vars['shelp'] = self.print_help
        self.update_vars(self.vars)
        self.print_help()

    def print_help(self):
        print
        self.p('Available Crawlmi objects:')
        for k, v in sorted(self.vars.iteritems()):
            if isinstance(v, self.relevant_classes):
                self.p('  %-10s %s' % (k, v))
        print
        self.p('Useful shortcuts:')
        self.p('  shelp()           Shell help (print this help)')
        self.p('  fetch(req_or_url) Fetch request (or URL) and update local objects')
        self.p('  view(response)    View response in a browser')

    def p(self, line=''):
        print "[c] %s" % line
