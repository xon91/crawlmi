import os

from twisted.trial import unittest

from crawlmi.tests import tests_datadir
from crawlmi.utils.settings import read_list_data_file


class UtilsSettingsTest(unittest.TestCase):
    def test_read_list_data_file(self):
        file_name = os.path.join(tests_datadir, 'list_data_file.txt')
        data = read_list_data_file(file_name)
        self.assertListEqual(data, ['a', 'b', 'c', 'f'])
