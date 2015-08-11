'''
Middleware to use Tor proxy (https://www.torproject.org/) for downloading.
Requests are not directly sent to Tor, though. They need to be sent thought
some http proxy, such as Privoxy (http://www.privoxy.org/).

To configure Provoxy with Tor see: http://www.privoxy.org/faq/misc.html#TOR
'''

import socket

from crawlmi import log
from crawlmi.exceptions import NotConfigured
from crawlmi.signals import Signal


# send this signal to set a new identity
new_tor_identity = Signal('new_tor_identity')


class Tor(object):
    def __init__(self, engine):
        settings = engine.settings
        self.tor_proxy = settings.get('TOR_HTTP_PROXY')
        if not self.tor_proxy:
            raise NotConfigured()
        self.tor_connection = settings.get('TOR_CONNECTION')
        self.tor_password = settings.get('TOR_PASSWORD')
        engine.signals.connect(self.new_tor_identity, signal=new_tor_identity)

    def process_request(self, request):
        if request.proxy is None:
            request.proxy = self.tor_proxy
            log.msg(format='Using tor for request %(request)s',
                    level=log.DEBUG, request=request)
        return request

    def new_tor_identity(self):
        '''Sets new tor identity.
        '''
        if self.tor_connection is None or self.tor_password is None:
            log.msg(format='Unable to set new tor identity.',
                    level=log.WARNING)
            return

        s = socket.socket()
        s.connect(self.tor_connection)
        s.send('AUTHENTICATE "%s"\r\n' % self.tor_password)
        resp = s.recv(1024)
        if resp.startswith('250'):
            s.send('signal NEWNYM\r\n')
            resp = s.recv(1024)
            if resp.startswith('250'):
                log.msg(format='New tor identity set', level=log.INFO)
            else:
                log.msg(format='Error 1 when setting new tor identity: %(resp)s',
                        level=log.WARNING, resp=resp)
        else:
            log.msg(format='Error 2 when setting new tor identity: %(resp)s',
                    level=log.WARNING, resp=resp)
