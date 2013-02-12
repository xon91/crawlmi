import random
import unittest2

from crawlmi.queue.memory_queue import MemoryQueue
from crawlmi.queue.priority_queue import PriorityQueue


def qfactory(priority):
    return MemoryQueue()


class PriorityQueueTest(unittest2.TestCase):

    def test_basic(self):
        q = PriorityQueue(qfactory)
        self.assertEqual(len(q), 0)
        self.assertRaises(IndexError, q.peek)
        self.assertRaises(IndexError, q.pop)
        q.push(42, 42)
        self.assertEqual(len(q), 1)
        self.assertEqual(q.peek(), 42)
        q.push(47, 47)
        self.assertEqual(len(q), 2)
        self.assertEqual(q.peek(), 47)

        self.assertEqual(q.pop(), 47)
        self.assertEqual(q.peek(), 42)
        self.assertEqual(q.pop(), 42)
        self.assertRaises(IndexError, q.pop)
        self.assertEqual(len(q), 0)

    def test_inactive(self):
        q = PriorityQueue(qfactory)
        self.assertEqual(len(q._active_queues), 0)
        self.assertEqual(len(q._inactive_queues), 0)
        q.push(1, 1)
        self.assertEqual(len(q._active_queues), 1)
        self.assertEqual(len(q._inactive_queues), 0)
        q.pop()
        self.assertEqual(len(q._active_queues), 0)
        self.assertEqual(len(q._inactive_queues), 1)
        q.push(2, 2)
        self.assertEqual(len(q._active_queues), 1)
        self.assertEqual(len(q._inactive_queues), 1)
        q.push(1, 3)
        self.assertEqual(len(q._active_queues), 2)
        self.assertEqual(len(q._inactive_queues), 0)

    def test_close(self):
        q = PriorityQueue(qfactory)
        q.push(1, 1)
        self.assertEqual(len(q), 1)
        q.close()
        self.assertRaises(RuntimeError, q.push, 10)
        self.assertRaises(RuntimeError, q.pop)
        self.assertRaises(RuntimeError, q.peek)
        self.assertRaises(RuntimeError, q.close)
        self.assertRaises(RuntimeError, len, q)

    def _pop_all(self, q):
        steps = len(q)
        return [q.pop() for i in xrange(steps)]

    def test_duplicate(self):
        q = PriorityQueue(qfactory)
        q.push(1, 'a')
        q.push(1, 'b')
        self.assertEqual(len(q), 2)
        q.push(2, 'c')
        q.push(3, 'd')
        q.push(2, 'e')
        q.push(3, 'f')
        self.assertEqual(len(q), 6)
        self.assertListEqual(self._pop_all(q), ['d', 'f', 'c', 'e', 'a', 'b'])

    def test_random_case(self):
        rnd = random.Random(47)
        q = PriorityQueue(qfactory)
        values = []
        operations = []
        for step in xrange(100):
            if len(q) and rnd.randint(1, 3) == 1:
                operations.append('pop')
                self.assertEqual(values.pop()[1], q.pop(), operations)
                if values:
                    self.assertEqual(values[-1][1], q.peek(), operations)
            else:
                v = rnd.randint(1, 50)
                q.push(v, -step)
                values.append((v, -step))
                operations.append('add %s' % v)
                values.sort()
                self.assertEqual(values[-1][1], q.peek(), operations)
            self.assertEqual(len(q), len(values), operations)
            active = set(q._active_queues)
            inactive = set(q._inactive_queues)
            self.assertSetEqual(active & inactive, set())
