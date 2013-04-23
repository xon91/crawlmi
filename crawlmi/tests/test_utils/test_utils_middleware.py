from twisted.trial import unittest

from crawlmi.utils.middleware import camelcase_to_capital


class UtilsMiddlewareTest(unittest.TestCase):
    def test_camelcase_to_capital(self):
        self.assertEqual(camelcase_to_capital('CamelCase'), 'CAMEL_CASE')
        self.assertEqual(camelcase_to_capital('CamelCamelCase'), 'CAMEL_CAMEL_CASE')
        self.assertEqual(camelcase_to_capital('Camel2Camel2Case'), 'CAMEL2_CAMEL2_CASE')
        self.assertEqual(camelcase_to_capital('getHTTPResponseCode'), 'GET_HTTP_RESPONSE_CODE')
        self.assertEqual(camelcase_to_capital('get2HTTPResponseCode'), 'GET2_HTTP_RESPONSE_CODE')
        self.assertEqual(camelcase_to_capital('HTTPResponseCode'), 'HTTP_RESPONSE_CODE')
        self.assertEqual(camelcase_to_capital('HTTPResponseCodeXYZ'), 'HTTP_RESPONSE_CODE_XYZ')
