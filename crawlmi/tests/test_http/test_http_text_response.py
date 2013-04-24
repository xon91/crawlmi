from twisted.trial import unittest

from crawlmi.http import TextResponse


class TextResponseTest(unittest.TestCase):
    def test_encoding(self):
        original_string = '''<meta http-equiv="content-type" content="text/html;charset=UTF-8" />'''
        unicode_string = original_string.decode('utf-8')
        response = TextResponse('', body=original_string)
        self.assertEqual(response.encoding, 'utf-8')
        self.assertIsInstance(response.text, unicode)
        self.assertEqual(response.text, unicode_string)

    def test_init_encoding(self):
        unicode_string = u'\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442'
        original_string = unicode_string.encode('cp1251')
        response = TextResponse('', body=original_string, encoding='cp1251')
        self.assertEqual(response.encoding, 'cp1251')
        self.assertEqual(response.text, unicode_string)

    def test_replace(self):
        original_string = '''<meta http-equiv="content-type" content="text/html;charset=UTF-8" />'''
        unicode_string = original_string.decode('utf-8')
        response = TextResponse('', body=original_string)
        self.assertEqual(response.encoding, 'utf-8')

        response2 = response.copy()
        self.assertIsInstance(response2, TextResponse)
        self.assertEqual(response2._encoding, response._encoding)
        self.assertEqual(response2._unicode_body, response._unicode_body)

        response3 = response.replace(encoding='cp1251')
        self.assertEqual(response3._encoding, 'cp1251')
        self.assertIsNone(response3._unicode_body)

        response4 = response.replace(body='hello')
        self.assertIsNone(response4._encoding)
        self.assertIsNone(response4._unicode_body)
