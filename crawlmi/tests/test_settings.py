import unittest2

from crawlmi.settings.settings import Settings


class SettingsTest(unittest2.TestCase):
    tests = {
        'BOOL_TRUE_1': (1, True),
        'BOOL_TRUE_2': ('1', True),
        'BOOL_TRUE_3': (True, True),
        'BOOL_FALSE_1': (0, False),
        'BOOL_FALSE_2': ('0', False),
        'BOOL_FALSE_3': (False, False),
        'BOOL_FALSE_4': (None, False),

        'INT_1': (0, 0),
        'INT_2': ('1', 1),
        'INT_3': ('-1', -1),
        'INT_4': (4.5, 4),

        'FLOAT_1': (0.0, 0.0),
        'FLOAT_2': ('5.4', 5.4),
        'FLOAT_3': (47, 47.0),
        'FLOAT_4': ('47.3', 47.3),

        'LIST_1': (['one', 'two'], ['one', 'two']),
        'LIST_2': ('one,two', ['one', 'two']),
        'LIST_3': ('one', ['one']),
        'LIST_4': ('', ['']),
    }

    def setUp(self):
        values = {}
        for (k, v) in self.tests.iteritems():
            values[k] = v[0]
        self.settings = Settings(values=values)

    def test_init(self):
        s1, s2 = Settings(), Settings()
        self.assertIsNot(s1.values, s2.values)
        values = {'1': '2'}
        s3 = Settings(values)
        self.assertIsNot(s3.values, values)

        self.assertTrue('1' in s3)
        self.assertFalse('2' in s3)
        self.assertEqual(s3['1'], '2')
        self.assertEqual(s3.get('1'), '2')
        self.assertEqual(s3.get('1', '3'), '2')
        self.assertIsNone(s3.get('2'))
        self.assertEqual(s3.get('2', '3'), '3')

    def _get_answers(self, prefix):
        result = []
        for (k, v) in self.tests.iteritems():
            if k.startswith(prefix):
                result.append((k, v[1]))
        return result

    def test_bool(self):
        for (k, v) in self._get_answers('BOOL'):
            self.assertIs(self.settings.get_bool(k), v, k)
        self.assertIs(self.settings.get_bool('invalid'), False)
        self.assertIs(self.settings.get_bool('invalid', True), True)
        self.assertRaises(ValueError, self.settings.get_bool, 'invalid', 'hello')

    def test_int(self):
        for (k, v) in self._get_answers('INT'):
            self.assertEqual(self.settings.get_int(k), v, k)
        self.assertEqual(self.settings.get_int('invalid'), 0)
        self.assertEqual(self.settings.get_int('invalid', 12), 12)
        self.assertRaises(ValueError, self.settings.get_int, 'invalid', 'hello')

    def test_float(self):
        for (k, v) in self._get_answers('FLOAT'):
            self.assertEqual(self.settings.get_float(k), v, k)
        self.assertEqual(self.settings.get_float('invalid'), 0.0)
        self.assertEqual(self.settings.get_float('invalid', 12.3), 12.3)
        self.assertRaises(ValueError, self.settings.get_float, 'invalid', 'hello')

    def test_list(self):
        for (k, v) in self._get_answers('LIST'):
            self.assertEqual(self.settings.get_list(k), v, k)
        self.assertEqual(self.settings.get_list('invalid'), [])

        listA = [1, 2, 3]
        self.assertIs(self.settings.get_list('invalid', listA), listA)
        listB = []
        self.assertIs(self.settings.get_list('invalid', listB), listB)