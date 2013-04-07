from twisted.trial import unittest

from crawlmi.utils.template import string_camelcase


class UtilsTemplateTest(unittest.TestCase):
    def test_string_camelcase(self):
        self.assertEqual(string_camelcase('lost-pound'), 'LostPound')
        self.assertEqual(string_camelcase('missing_images'), 'MissingImages')
