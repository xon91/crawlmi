from collections import defaultdict

from crawlmi.signals import Signal
from crawlmi.utils.request import request_fingerprint


# send this signal to clear the filter's storage
# args: [df_tag]
clear_duplicate_filter = Signal('clear_duplicate_filter')


class DuplicateFilter(object):
    def __init__(self, engine):
        self.fingerprints = defaultdict(set)
        engine.signals.connect(self.clear_duplicate_filter,
                               signal=clear_duplicate_filter)

    def process_request(self, request):
        df_tag = request.meta.get('df_tag')
        fps = self.fingerprints[df_tag]
        fp = request_fingerprint(request)
        if fp in fps:
            return
        fps.add(fp)
        return request

    def clear_duplicate_filter(self, df_tag=None):
        if df_tag in self.fingerprints:
            del self.fingerprints[df_tag]
