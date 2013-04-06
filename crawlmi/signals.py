class Signal(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Signal: %s>' % self.name


# invoked when engine is running and happy to download
# args:
engine_started = Signal('engine_started')
# invoked when engine is about to be stopped. Engine is still running, though.
# args: reason
engine_stopping = Signal('engine_stopping')
# invoked when engine stopped and is not running anymore.
# args: reason
engine_stopped = Signal('engine_stopped')

# invoked when the request successfully passes through downloader pipeline.
# args: request
request_received = Signal('request_received')
# invoked when the response is popped out of the outq
# args: response (either Response or Failure)
response_downloaded = Signal('response_downloaded')
# invoked when the response successfully passes through downloader pipeline
# args: response (either Response or Failure)
response_received = Signal('response_received')
# invoked when spider does not process the Failure received either from
# downloader or the pipeline, or raised inside the spider
# args: failure
spider_error = Signal('spider_error')
