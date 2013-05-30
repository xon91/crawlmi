import random

from twisted.trial import unittest

from crawlmi.stats.top_samples import TopSamples


class TopSamplesTest(unittest.TestCase):
    def test_size_1(self):
        ts = TopSamples(size=1)
        ts.add_sample(1, 'hello')
        self.assertEqual(len(ts), 1)
        self.assertListEqual(ts.samples, [(1, 'hello')])
        ts.add_sample(0, 'world')
        self.assertEqual(len(ts), 1)
        self.assertListEqual(ts.samples, [(1, 'hello')])
        ts.add_sample(2, '!')
        self.assertEqual(len(ts), 1)
        self.assertListEqual(ts.samples, [(2, '!')])

    def test_default_size(self):
        ts = TopSamples()
        objects = [(i, 2 * i) for i in xrange(20)]
        random.shuffle(objects)
        for (p, v) in objects:
            ts.add_sample(p, v)
        self.assertEqual(len(ts), 5)
        self.assertListEqual(ts.samples, [(19, 38), (18, 36), (17, 34), (16, 32), (15, 30)])
        # test - requesting the values doesn't screw anything
        self.assertEqual(len(ts), 5)
        self.assertListEqual(ts.samples, [(19, 38), (18, 36), (17, 34), (16, 32), (15, 30)])
