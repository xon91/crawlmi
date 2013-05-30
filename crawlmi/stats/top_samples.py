from crawlmi.queue import Heap


class TopSamples(object):
    '''Stores the top `size` objects with the highest priorities.
    Useful to store the top N largest sites, for example.
    '''

    def __init__(self, size=5):
        self.size = size
        self._heap = Heap()

    def add_sample(self, priority, value):
        # negate priority, so that the smallest ones are on top and first to pop
        self._heap.push((-priority, value))
        if len(self._heap) > self.size:
            self._heap.pop()

    @property
    def samples(self):
        objects = []
        while self._heap:
            objects.append(self._heap.pop())
        map(self._heap.push, objects)
        return [(-p, v) for (p, v) in reversed(objects)]

    def __len__(self):
        return len(self._heap)

    def __str__(self):
        return '\n    '.join(map(str, self.samples))
    __repr__ = __str__
