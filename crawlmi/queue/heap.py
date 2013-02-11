from .queue import Queue


class Heap(Queue):
    '''Implementation of the binary heap.
    Biggest values are on the top of the heap.
    Order of the same values is not guaranteed.
    '''

    def __init__(self):
        super(Heap, self).__init__()
        self._heap = [None]

    def _push(self, value):
        self._heap.append(value)
        self._heapify_up(len(self._heap) - 1)

    def _peek(self):
        return self._heap[1]

    def _pop(self):
        result, self._heap[1] = self._heap[1], self._heap[-1]
        del self._heap[-1:]

        if len(self._heap) > 1:
            self._heapify_down(1)
        return result

    def _close(self):
        del self._heap

    def _heapify_down(self, index):
        while True:
            child = (index << 1)
            if child >= len(self._heap):
                break
            if (child + 1 < len(self._heap) and
                    self._heap[child] < self._heap[child + 1]):
                child += 1
            if self._heap[index] >= self._heap[child]:
                break
            self._heap[index], self._heap[child] = \
                self._heap[child], self._heap[index]
            index = child

    def _heapify_up(self, index):
        while index > 1:
            parent = (index >> 1)
            if self._heap[parent] >= self._heap[index]:
                break
            self._heap[parent], self._heap[index] = \
                self._heap[index], self._heap[parent]
            index = parent
