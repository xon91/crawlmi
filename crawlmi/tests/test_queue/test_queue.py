from twisted.trial import unittest

from crawlmi.queue import MemoryQueue


class QueueTest(unittest.TestCase):

    def _test(self, qcls):
        q = qcls()
        self.assertEqual(len(q), 0)
        self.assertFalse(q)
        q.push(1)
        q.push(2)
        q.push(3)
        self.assertEqual(len(q), 3)
        self.assertTrue(q)
        self.assertEqual(q.peek(), 1)
        self.assertEqual(len(q), 3)
        self.assertEqual(q.pop(), 1)
        self.assertEqual(q.pop(), 2)
        self.assertEqual(len(q), 1)
        self.assertEqual(q.pop(), 3)
        self.assertRaises(IndexError, q.peek)
        self.assertRaises(IndexError, q.pop)
        self.assertEqual(len(q), 0)
        self.assertFalse(q)
        q.push(47)
        self.assertEqual(len(q), 1)
        self.assertEqual(q.peek(), 47)
        self.assertEqual(q.pop(), 47)

        # closing
        q.close()
        self.assertRaises(RuntimeError, q.push, 10)
        self.assertRaises(RuntimeError, q.pop)
        self.assertRaises(RuntimeError, q.peek)
        self.assertRaises(RuntimeError, q.close)
        self.assertRaises(RuntimeError, len, q)

    def test_memory_queue(self):
        self._test(MemoryQueue)
