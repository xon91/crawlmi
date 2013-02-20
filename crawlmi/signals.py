engine_started = object()
engine_stopped = object()

# called when the request is pushed into the inq
request_received = object()
# called when the response is popped out of the outq
response_received = object()
