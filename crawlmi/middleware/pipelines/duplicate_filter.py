from crawlmi.utils.request import request_fingerprint


class DuplicateFilter(object):
    def __init__(self, engine):
        self.fingerprints = set()

    def process_request(self, request):
        fp = request_fingerprint(request)
        if fp in self.fingerprints:
            return
        self.fingerprints.add(fp)
        return request
