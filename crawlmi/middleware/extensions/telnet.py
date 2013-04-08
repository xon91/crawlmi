'''Crawlmi Telnet console extension.
'''

import pprint

from twisted.conch import manhole, telnet
from twisted.conch.insults import insults
from twisted.internet import protocol

from crawlmi import log, signals
from crawlmi.signals import Signal
from crawlmi.utils.engine import print_engine_status
from crawlmi.utils.tcp import listen_tcp
from crawlmi.utils.trackref import print_live_refs

try:
    import guppy
    hpy = guppy.hpy()
except ImportError:
    hpy = None

# signal to update telnet variables
# args: telnet_vars
update_telnet_vars = Signal('update_telnet_vars')


class TelnetConsole(protocol.ServerFactory):
    def __init__(self, engine):
        self.engine = engine
        self.noisy = False
        self.portrange = map(int, engine.settings.get_list('TELNET_CONSOLE_PORT'))
        self.host = engine.settings['TELNET_CONSOLE_HOST']
        engine.signals.connect(self.start_listening, signals.engine_started)
        engine.signals.connect(self.stop_listening, signals.engine_stopped)

    def start_listening(self):
        self.port = listen_tcp(self.portrange, self.host, self)
        h = self.port.getHost()
        log.msg(format='Telnet console listening on %(host)s:%(port)d',
                level=log.DEBUG, host=h.host, port=h.port)

    def stop_listening(self):
        self.port.stopListening()

    def protocol(self):
        telnet_vars = self._get_telnet_vars()
        return telnet.TelnetTransport(
            telnet.TelnetBootstrapProtocol,
            insults.ServerProtocol, manhole.Manhole, telnet_vars)

    def _get_telnet_vars(self):
        telnet_vars = {
            'engine': self.engine,
            'spider': self.engine.spider,
            'stats': self.engine.stats,
            'settings': self.engine.settings,
            'est': lambda: print_engine_status(self.engine),
            'p': pprint.pprint,
            'prefs': print_live_refs,
            'hpy': hpy,
            'help': 'This is crawlmi telnet console.',
        }
        self.engine.signals.send(update_telnet_vars, telnet_vars=telnet_vars)
        return telnet_vars
