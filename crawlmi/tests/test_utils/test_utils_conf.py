import os

from twisted.trial import unittest

from crawlmi.tests import tests_datadir
from crawlmi.utils.conf import (build_component_list, arglist_to_dict,
                                read_list_data_file)


class UtilsConfTest(unittest.TestCase):

    def test_build_component_list(self):
        base = {'one': 1, 'two': 2, 'three': 3, 'five': 5, 'six': None}
        custom = {'two': None, 'three': 8, 'four': 4}
        self.assertEqual(build_component_list(base, custom),
                         ['one', 'four', 'five', 'three'])

        custom = ['a', 'b', 'c']
        self.assertEqual(build_component_list(base, custom), custom)

    def test_arglist_to_dict(self):
        self.assertEqual(
            arglist_to_dict(['arg1=val1', 'arg2=val2']),
            {'arg1': 'val1', 'arg2': 'val2'})

    def test_read_list_data_file(self):
        file_name = os.path.join(tests_datadir, 'list_data_file.txt')
        data = read_list_data_file(file_name)
        self.assertListEqual(data, ['a', 'b', 'c', 'f'])
