from .memory_queue import MemoryQueue
from crawlmi.http import Response


class ResponseQueue(MemoryQueue):
    def __init__(self, active_size_limit=0):
        super(ResponseQueue, self).__init__()
        self.active_size_limit = active_size_limit
        self.active_size = 0

    def _push(self, response):
        super(ResponseQueue, self)._push(response)
        if isinstance(response, Response):
            self.active_size += len(response.body)

    def _pop(self):
        response = super(ResponseQueue, self)._pop()
        if isinstance(response, Response):
            self.active_size -= len(response.body)
        return response

    def needs_backout(self):
        return (self.active_size_limit and
                self.active_size >= self.active_size_limit)
