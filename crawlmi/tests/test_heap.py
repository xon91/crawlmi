import random
import unittest2

from crawlmi.queue import Heap


class HeapTest(unittest2.TestCase):
    def test_basic(self):
        h = Heap()
        self.assertEqual(len(h), 0)
        self.assertRaises(IndexError, h.peek)
        self.assertRaises(IndexError, h.pop)
        h.push(42)
        self.assertEqual(len(h), 1)
        self.assertEqual(h.peek(), 42)
        h.push(47)
        self.assertEqual(len(h), 2)
        self.assertEqual(h.peek(), 47)

        self.assertEqual(h.pop(), 47)
        self.assertEqual(h.peek(), 42)
        self.assertEqual(h.pop(), 42)
        self.assertRaises(IndexError, h.pop)
        self.assertEqual(len(h), 0)

    def test_close(self):
        h = Heap()
        h.push(1)
        h.push(2)
        h.push(3)
        self.assertEqual(len(h), 3)
        h.close()
        self.assertRaises(RuntimeError, h.push, 10)
        self.assertRaises(RuntimeError, h.pop)
        self.assertRaises(RuntimeError, h.peek)
        self.assertRaises(RuntimeError, h.close)
        self.assertRaises(RuntimeError, len, h)

    def _pop_all(self, q):
        steps = len(q)
        return [q.pop() for i in xrange(steps)]

    def test_duplicite_case(self):
        h = Heap()
        h.push(1)
        h.push(1)
        self.assertEqual(len(h), 2)
        h.push(2)
        h.push(3)
        h.push(2)
        h.push(3)
        self.assertEqual(len(h), 6)
        self.assertListEqual(self._pop_all(h), [3, 3, 2, 2, 1, 1])

    def test_random_case(self):
        rnd = random.Random(47)
        h = Heap()
        values = []
        operations = []
        for step in xrange(100):
            if len(h) and rnd.randint(1, 3) == 1:
                operations.append('pop')
                self.assertEqual(values.pop(), h.pop(), operations)
                if values:
                    self.assertEqual(values[-1], h.peek(), operations)
            else:
                v = rnd.randint(1, 50)
                h.push(v)
                values.append(v)
                operations.append('add %s' % v)
                values.sort()
                self.assertEqual(values[-1], h.peek(), operations)
            self.assertEqual(len(h), len(values), operations)
