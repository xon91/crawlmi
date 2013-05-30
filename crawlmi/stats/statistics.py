import math


class Statistics(object):
    '''Statistics calculates the basic statistics about the set of
    weighted values.
    '''

    def __init__(self):
        self.sum_values = 0.0
        # sum of of the squared values - used to calculate variance and std_dev
        self.sum_values_2 = 0.0
        self.sum_weights = 0.0
        self.minimum = None
        self.maximum = None

    def add_value(self, value, weight=1.0):
        if weight <= 0.0:
            raise ValueError('Weight must be a positive value.')
        self.sum_values += value * weight
        self.sum_values_2 += value * value * weight
        self.sum_weights += weight
        self.minimum = min(self.minimum, value) if self.minimum is not None else value
        self.maximum = max(self.maximum, value) if self.maximum is not None else value

    @property
    def empty(self):
        return self.sum_weights == 0

    @property
    def average(self):
        if self.empty:
            return None
        return self.sum_values / self.sum_weights

    @property
    def variance(self):
        if self.empty:
            return None
        avg = self.average
        avg2 = self.sum_values_2 / self.sum_weights
        return avg2 - avg * avg

    @property
    def std_dev(self):
        '''No more than 1/k^2 of the distribution's values can be more than k
        standard deviations away from the mean.
        '''
        if self.empty:
            return None
        return math.sqrt(self.variance)

    def __str__(self):
        return ('Weights: %.1f Avg: %.1f Std_dev: %.1f Minimum: %.1f Maximum: %.1f' %
            (self.sum_weights, self.average, self.std_dev, self.minimum, self.maximum))
    __repr__ = __str__
