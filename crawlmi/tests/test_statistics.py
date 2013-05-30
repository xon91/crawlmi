from twisted.trial import unittest

from crawlmi.stats.statistics import Statistics
from crawlmi.utils.test import eq


class StatisticsTest(unittest.TestCase):
    def setUp(self):
        self.stats = Statistics()

    def add_values(self, values):
        for x in values:
            if hasattr(x, '__iter__'):
                value, weight = x
            else:
                value, weight = x, 1.0
            self.stats.add_value(value, weight)

    def test_basic(self):
        self.add_values([(5, 1.0), (10, 2.0), (2, 0.5), (0, 0.1), (-3, 0.2)])
        self.assertFalse(self.stats.empty)
        self.assertTrue(eq(self.stats.sum_weights, 3.8), self.stats.sum_weights)
        self.assertTrue(eq(self.stats.sum_values, 25.4), self.stats.sum_values)
        self.assertTrue(eq(self.stats.average, 6.6842105263157894736842105263158), self.stats.average)
        self.assertEqual(self.stats.minimum, -3)
        self.assertEqual(self.stats.maximum, 10)

    def test_simple(self):
        self.add_values([(3, 1.5)])
        self.assertTrue(eq(self.stats.sum_weights, 1.5), self.stats.sum_weights)
        self.assertTrue(eq(self.stats.sum_values, 4.5), self.stats.sum_values)
        self.assertTrue(eq(self.stats.average, 3), self.stats.average)
        self.assertTrue(eq(self.stats.variance, 0), self.stats.variance)
        self.assertTrue(eq(self.stats.std_dev, 0), self.stats.std_dev)
        self.assertEqual(self.stats.minimum, 3)
        self.assertEqual(self.stats.maximum, 3)

    def test_empty(self):
        self.assertTrue(self.stats.empty)
        self.assertIsNone(self.stats.average)
        self.assertIsNone(self.stats.minimum)
        self.assertIsNone(self.stats.maximum)
        self.assertIsNone(self.stats.variance)
        self.assertIsNone(self.stats.std_dev)

    def test_negative_weight(self):
        self.assertRaises(ValueError, self.stats.add_value, 0, -0.1)
        self.assertRaises(ValueError, self.stats.add_value, 3, 0)

    def test_variance(self):
        # example taken from http://en.wikipedia.org/wiki/Standard_deviation
        self.add_values([2, 4, 4, 4, 5, 5, 7, 9])
        self.assertTrue(eq(self.stats.variance, 4), self.stats.variance)
        self.assertTrue(eq(self.stats.std_dev, 2), self.stats.std_dev)
