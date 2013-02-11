class Queue(object):

    def __init__(self):
        self._closed = False
        self._num_objects = 0

    def push(self, value):
        if self._closed:
            raise RuntimeError('pushing to already closed queue')
        self._num_objects += 1
        self._push(value)

    def peek(self):
        if self._closed:
            raise RuntimeError('peeking already closed queue')
        if self._num_objects == 0:
            raise IndexError('peeking in empty queue')
        return self._peek()

    def pop(self):
        if self._closed:
            raise RuntimeError('popping from already closed queue')
        if self._num_objects == 0:
            raise IndexError('popping from empty qeueue')
        self._num_objects -= 1
        return self._pop()

    def close(self):
        if self._closed:
            raise RuntimeError('closing already closed queue')
        self._closed = True
        self._close()

    def __len__(self):
        if self._closed:
            raise RuntimeError('`len` on already closed queue')
        return self._num_objects

    def _push(self):
        raise NotImplementedError()

    def _peek(self):
        raise NotImplementedError()

    def _pop(self):
        raise NotImplementedError()

    def _close(self):
        raise NotImplementedError()
