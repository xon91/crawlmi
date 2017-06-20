from pprint import pprint
import signal
import traceback

from twisted.internet import reactor, threads
import xextract

from crawlmi.http import Request, Response
from crawlmi.utils.console import start_python_console
from crawlmi.utils.request import request_deferred
from crawlmi.utils.response import open_in_browser
from crawlmi.utils.url import any_to_uri


class Shell(object):
    def __init__(self, engine, update_vars=None):
        self.engine = engine
        self.engine.stop_if_idle = False
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

        response = None
        try:
            response = threads.blockingCallFromThread(reactor, self._schedule, request)
        except:
            traceback.print_exc()
        self.populate_vars(request, response)

    def _schedule(self, request):
        d = request_deferred(request)
        self.engine.download(request)
        return d

    def populate_vars(self, request=None, response=None):
        self.vars['engine'] = self.engine
        self.vars['settings'] = self.engine.settings
        self.vars['spider'] = self.engine.spider
        self.vars['request'] = request
        self.vars['response'] = response
        self.vars['fetch'] = self.fetch
        self.vars['view'] = open_in_browser
        self.vars['shelp'] = self.print_help
        self.vars.update(
            (v, getattr(xextract, v))
            for v in xextract.parsers.__all__)

        # some useful objects
        self.vars['Request'] = Request
        self.vars['Response'] = Response
        self.vars.setdefault('pprint', pprint)
        self.print_vars = set(self.update_vars(self.vars) or [])
        self.print_vars |= set(['engine', 'settings', 'spider', 'request', 'response'])
        self.print_vars |= set(xextract.parsers.__all__)
        self.print_help()

    def print_help(self):
        print
        self.p('Available Crawlmi objects:')
        for k, v in sorted(self.vars.iteritems()):
            if v is not None and k in self.print_vars:
                self.p('  %-10s %s' % (k, v))
        print
        self.p('Useful shortcuts:')
        self.p('  shelp()           Shell help (print this help)')
        self.p('  fetch(req_or_url) Fetch request (or URL) and update local objects')
        self.p('  view(response)    View response in a browser')
        self.p('  xextract parsers  %s' % ', '.join(xextract.parsers.__all__))

    def p(self, line=''):
        print "[c] %s" % line
