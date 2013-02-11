from collections import deque

from .queue import Queue


class MemoryQueue(Queue):
    def __init__(self):
        super(MemoryQueue, self).__init__()
        self.storage = deque()

    def _push(self, value):
        self.storage.append(value)

    def _peek(self):
        return self.storage[0]

    def _pop(self):
        return self.storage.popleft()

    def _close(self):
        del self.storage
