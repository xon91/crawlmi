class Queue(object):
    '''Base class for the queue object.
    It implements the boilerplate code:
        - keep track of the number of stored objects
        - forbid operations on closed queue
        - forbid peeking and popping from empty queue
    Child classes only need to implement _push, _peek, _pop and _close.
    '''

    def __init__(self):
        self._closed = False
        self._num_objects = 0

    def push(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError('pushing to already closed queue')
        self._num_objects += 1
        self._push(*args, **kwargs)

    def peek(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError('peeking already closed queue')
        if self._num_objects == 0:
            raise IndexError('peeking in empty queue')
        return self._peek(*args, **kwargs)

    def pop(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError('popping from already closed queue')
        if self._num_objects == 0:
            raise IndexError('popping from empty qeueue')
        self._num_objects -= 1
        return self._pop(*args, **kwargs)

    def close(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError('closing already closed queue')
        self._closed = True
        self._close(*args, **kwargs)

    def __len__(self):
        if self._closed:
            raise RuntimeError('`len` on already closed queue')
        return self._num_objects

    def _push(self, *args, **kwargs):
        raise NotImplementedError()

    def _peek(self, *args, **kwargs):
        raise NotImplementedError()

    def _pop(self, *args, **kwargs):
        raise NotImplementedError()

    def _close(self, *args, **kwargs):
        raise NotImplementedError()
