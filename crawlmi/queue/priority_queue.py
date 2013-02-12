from .heap import Heap
from .queue import Queue


class PriorityQueue(Queue):
    '''Implementation of the priority queue with the following properties:
        - objects with the higher `priority` are popped first
        - objects with the same `priority` are popped in the FIFO order

    Implementation combines the asymptotic speed of the heap with the practical
    speed of the ordinary queue. In other words, it works pretty fast, when
    there are many different priorities and even faster, when there are only
    few different priorities.

    PriorityQueue internally uses the implementation of the ordinary queue,
    defined through `qfactory`. Internal queue has to inherit from `Queue`.

    The constructor receives a `qfactory` argument, which is a callable used to
    instantiate a new (internal) queue when a new priority is allocated. The
    `qfactory` function is called with the priority number as first and only
    argument.
    '''

    def __init__(self, qfactory):
        super(PriorityQueue, self).__init__()
        self.qfactory = qfactory
        self._heap = Heap()
        self._active_queues = {}
        self._inactive_queues = {}

    def _push(self, priority, value):
        if priority not in self._active_queues:
            self._heap.push(priority)
            if priority in self._inactive_queues:
                self._active_queues[priority] = self._inactive_queues[priority]
                del self._inactive_queues[priority]
            else:
                self._active_queues[priority] = self.qfactory(priority)
        self._active_queues[priority].push(value)

    def _peek(self):
        top_priority = self._heap.peek()
        return self._active_queues[top_priority].peek()

    def _pop(self):
        top_priority = self._heap.peek()
        q = self._active_queues[top_priority]
        result = q.pop()
        if len(q) == 0:
            self._inactive_queues[top_priority] = q
            del self._active_queues[top_priority]
            self._heap.pop()
        return result

    def _close(self):
        for p, q in self._active_queues.iteritems():
            q.close()
        del self._active_queues
        for p, q in self._inactive_queues.iteritems():
            q.close()
        del self._inactive_queues
        self._heap.close()
        del self._heap
