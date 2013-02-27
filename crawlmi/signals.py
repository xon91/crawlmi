# invoked when engine is running and happy to download
# args:
engine_started = object()
# invoked when engine is about to be stopped. Engine is still running, though.
# args:
engine_stopping = object()
# invoked when engine stopped and is not running anymore.
# args:
engine_stopped = object()

# invoked when the request successfully passes through downloader pipeline.
# args: request
request_received = object()
# invoked when the response is popped out of the outq
# args: response (either Response or Failure)
response_downloaded = object()
# invoked when the response successfully passes through downloader pipeline
# args: response (either Response or Failure)
response_received = object()
# invoked when spider does not process the Failure received either from
# downloader or the pipeline, or raised inside the spider
# args: failure
spider_error = object()
