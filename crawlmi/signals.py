# args:
engine_started = object()
# args:
engine_stopped = object()

# invoked when the request successfully passes through downloader pipeline.
# args: request
request_received = object()
# invoked when the response is popped out of the outq
# args: response
response_downloaded = object()
# invoked when the response successfully passes through downloader pipeline
# args: response
response_received = object()
