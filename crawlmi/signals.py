class Signal(object):
    '''Signals don't have to be objects of this class, but it gives them
    a nice `repr()` method which useful for debugging.
    '''
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Signal: %s>' % self.name


# invoked when engine is running
# args:
engine_started = Signal('engine_started')
# invoked when engine stopped and is not running anymore.
# args: reason
engine_stopped = Signal('engine_stopped')

# invoked when the request successfully passes through downloader pipeline.
# args: request
request_received = Signal('request_received')
# invoked when the response was successfully downloaded and is popped out of
# the response_queue
# args: response
response_downloaded = Signal('response_downloaded')
# invoked when the response successfully passes through downloader pipeline
# args: response
response_received = Signal('response_received')
# invoked when the response or failure unsuccessfully passes through downloader
# pipeline
# args: failure
failure_received = Signal('failure_received')
# invoked when spider does not process the Failure received either from
# downloader or the pipeline, or raised inside the spider
# args: failure
spider_error = Signal('spider_error')

# invoked when there are no more requests to download.
# Either schedule new requests or raise DontStopEngine exception.
# args:
spider_idle = Signal('spider_idle')


# signals defined in other modules
from crawlmi.middleware.extensions.save_response import save_response
