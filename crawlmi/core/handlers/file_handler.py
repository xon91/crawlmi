'''Download file from local filesystem.'''

from twisted.internet import defer

from crawlmi.http.response import factory as resp_factory
from crawlmi.utils.url import file_uri_to_path


class FileDownloadHandler(object):

    def __init__(self, settings):
        pass

    def download_request(self, request):
        def download():
            filepath = file_uri_to_path(request.url)
            body = open(filepath, 'rb').read()
            response_cls = resp_factory.from_args(filename=filepath, body=body)
            return response_cls(url=request.url, body=body, request=request)
        return defer.maybeDeferred(download)
