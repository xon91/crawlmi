'''Download file from local filesystem.'''

from twisted.internet import defer

from crawlmi.http.response.response import Response
from crawlmi.utils.url import file_uri_to_path


class FileDownloadHandler(object):

    def __init__(self, settings):
        pass

    def download_request(self, request):
        def download():
            filepath = file_uri_to_path(request.url)
            body = open(filepath, 'rb').read()
            return Response(url=request.url, body=body, request=request)
        return defer.maybeDeferred(download)
