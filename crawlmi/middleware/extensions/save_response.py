from os.path import join
from pprint import pformat
import re
import time
from urlparse import urlparse

from crawlmi.exceptions import NotConfigured
from crawlmi.signals import Signal


# send this signal to save the resposne
# args: response [details] [filename] [dirname]
save_response = Signal('save_response')


class SaveResponse(object):
    def __init__(self, engine):
        self.engine = engine
        self.html_dir = engine.settings.get('SAVE_RESPONSE_DIR')
        if not self.html_dir:
            raise NotConfigured()
        engine.signals.connect(self.save_response, signal=save_response)

    def save_response(self, response, details='', filename=None, dirname=''):
        dirname = self.engine.project.data_path(join(self.html_dir, dirname),
                                                create_dir=True)

        parsed = urlparse(response.url)
        if filename is None:
            filename = re.sub(r'\W', '_', '%s%s-%s' %
                              (parsed.netloc, parsed.path, time.time()))
        # write html content
        with open(self._html_filename(dirname, filename), 'wb') as f:
            f.write(response.body)

        # write response info
        with open(self._info_filename(dirname, filename), 'wb') as f:
            request = response.request
            f.write('Spider: %s\n' % self.engine.spider)
            f.write('Request:\t%s\n' % request)
            f.write('Response:\t%s\n' % response)

            # response parts
            f.write('\nRESPONSE:\n')
            if hasattr(response, 'encoding'):
                self._write(f, 'Encoding', response.encoding)
            self._write(f, 'Headers', response.headers)
            self._write(f, 'Meta', response.meta)
            # request parts
            f.write('\nREQUEST:\n')
            self._write(f, 'History', request.history)
            self._write(f, 'Encoding', request.encoding)
            self._write(f, 'Proxy', request.proxy)
            self._write(f, 'Headers', request.headers)
            self._write(f, 'Method', request.method)
            self._write(f, 'Priority', request.priority)
            # additional details
            f.write('\nDetails:\n%s' % details)

    def _write(self, f, label, data):
        try:
            data = pformat(data)
        except:
            f.write('%s: <unable to serialize>\n' % label)
        else:
            f.write('%s: %s\n' % (label, data))

    def _html_filename(self, dirname, filename):
        return join(dirname, filename + '.html')

    def _info_filename(self, dirname, filename):
        return join(dirname, filename + '.info')
