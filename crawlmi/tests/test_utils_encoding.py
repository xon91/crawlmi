import codecs

from twisted.trial import unittest

from crawlmi.utils.encoding import (_read_bom, get_encoding_from_headers,
        get_encoding_from_content, _norm_encoding, get_unicode_from_response)
from crawlmi.http.headers import Headers


class EncodingDetectionTest(unittest.TestCase):
    def test_bom(self):
        # cjk water character in unicode
        water_unicode = u'\u6C34'
        # BOM + water character encoded
        utf16be = '\xfe\xff\x6c\x34'
        utf16le = '\xff\xfe\x34\x6c'
        utf32be = '\x00\x00\xfe\xff\x00\x00\x6c\x34'
        utf32le = '\xff\xfe\x00\x00\x34\x6c\x00\x00'
        for string in (utf16be, utf16le, utf32be, utf32le):
            bom_encoding, bom = _read_bom(string)
            decoded = string[len(bom):].decode(bom_encoding)
            self.assertEqual(water_unicode, decoded)
        # Body without BOM
        enc, bom = _read_bom('foo')
        self.assertEqual(enc, None)
        self.assertEqual(bom, None)
        # Empty body
        enc, bom = _read_bom('')
        self.assertEqual(enc, None)
        self.assertEqual(bom, None)

    def test_http_encoding_header(self):
        headers = Headers({'Content-Type': 'text/html; charset=ISO-8859-4'})
        self.assertEqual(get_encoding_from_headers(headers), 'iso8859-4')
        headers = Headers({'Something-else': 'text/html; charset=ISO-8859-4'})
        self.assertEqual(get_encoding_from_headers(headers), None)
        headers = Headers({'Content-Type': 'text/html'})
        self.assertEqual(get_encoding_from_headers(headers), 'cp1252')

    def test_html_body_declared_encoding(self):
        fragments = [
            # Content-Type as meta http-equiv
            '''<meta http-equiv="content-type" content="text/html;charset=UTF-8" />''',
            '''\n<meta http-equiv="Content-Type"\ncontent="text/html; charset=utf-8">''',
            '''<meta content="text/html; charset=utf-8"\n http-equiv='Content-Type'>''',
            ''' bad html still supported < meta http-equiv='Content-Type'\n content="text/html; charset=utf-8">''',
            # html5 meta charset
            '''<meta charset="utf-8">''',
            # xml encoding
            '''<?xml version="1.0" encoding="utf-8"?>''',
        ]
        for fragment in fragments:
            encoding = get_encoding_from_content(fragment)
            self.assertEqual(encoding, 'utf-8', fragment)
        self.assertEqual(None, get_encoding_from_content('something else'))
        self.assertEqual(None, get_encoding_from_content('''<head></head><body>this isn't searched<meta charset="utf-8">'''))
        self.assertEqual(None, get_encoding_from_content(
            '''<meta http-equiv="Fake-Content-Type-Header" content="text/html; charset=utf-8">'''))


class CodecsEncodingTest(unittest.TestCase):
    def test_resolve_encoding(self):
        self.assertEqual(_norm_encoding('latin1'), 'cp1252')
        self.assertEqual(_norm_encoding(' Latin-1'), 'cp1252')
        self.assertEqual(_norm_encoding('gb_2312-80'), 'gb18030')
        self.assertEqual(_norm_encoding('unknown encoding'), None)


class UnicodeDecodingTest(unittest.TestCase):
    def test_utf8(self):
        self.assertEqual(unicode('\xc2\xa3', 'utf-8', 'replace'), u'\xa3')

    def test_invalid_utf8(self):
        self.assertEqual(unicode('\xc2\xc2\xa3', 'utf-8', 'replace'), u'\ufffd\xa3')


def norm_encoding(enc):
    return codecs.lookup(enc).name


class MockResponse(object):
    def __init__(self, body, encoding):
        self.body = body
        self.headers = Headers()
        if encoding:
            self.headers['Content-Type'] = 'text/html; charset=' + encoding


class HtmlConversionTests(unittest.TestCase):

    def test_unicode_body(self):
        unicode_string = u'\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442'
        original_string = unicode_string.encode('cp1251')
        encoding, body_unicode = get_unicode_from_response(
            MockResponse(original_string, 'cp1251'))
        # check body_as_unicode
        self.assertTrue(isinstance(body_unicode, unicode))
        self.assertEqual(body_unicode, unicode_string)

    def _assert_encoding(self, body, http_encoding, expected_encoding,
                expected_unicode):
        encoding, body_unicode = get_unicode_from_response(
            MockResponse(body, http_encoding))
        self.assertTrue(isinstance(body_unicode, unicode))
        self.assertEqual(norm_encoding(encoding),
                norm_encoding(expected_encoding))
        self.assertEqual(body_unicode, expected_unicode)

    def test_content_type_and_conversion(self):
        '''Test content type header is interpreted and text converted as
        expected.
        '''
        self._assert_encoding('\xc2\xa3', 'utf-8', 'utf-8', u'\xa3')
        self._assert_encoding('\xa3', 'iso-8859-1', 'cp1252', u'\xa3')
        self._assert_encoding('\xc2\xa3', '', 'utf-8', u'\xa3')
        self._assert_encoding('\xc2\xa3', 'none', 'utf-8', u'\xa3')
        self._assert_encoding('\xa8D', 'gb2312', 'gb18030', u'\u2015')
        self._assert_encoding('\xa8D', 'gbk', 'gb18030', u'\u2015')

    def test_invalid_utf8_encoded_body_with_valid_utf8_BOM(self):
        # the BOM is stripped
        self._assert_encoding('\xef\xbb\xbfWORD\xe3\xab', 'utf-8',
                'utf-8', u'WORD\ufffd')
        self._assert_encoding('\xef\xbb\xbfWORD\xe3\xab', None,
                'utf-8', u'WORD\ufffd')

    def test_replace_wrong_encoding(self):
        '''Test invalid chars are replaced properly.'''
        encoding, body_unicode = get_unicode_from_response(
            MockResponse('PREFIX\xe3\xabSUFFIX', 'utf-8'))
        self.assertIn(u'\ufffd', body_unicode)
        self.assertIn(u'PREFIX', body_unicode)
        self.assertIn(u'SUFFIX', body_unicode)

        # Do not destroy html tags due to encoding bugs
        encoding, body_unicode = get_unicode_from_response(
            MockResponse('\xf0<span>value</span>', 'utf-8'))
        self.assertIn(u'<span>value</span>', body_unicode)

    def test_BOM(self):
        # utf-16 cases already tested, as is the BOM detection function

        # http header takes precedence, irrespective of BOM
        bom_be_str = codecs.BOM_UTF16_BE + u"hi".encode('utf-16-be')
        expected = u'\ufffd\ufffd\x00h\x00i'
        self._assert_encoding(bom_be_str, 'utf-8', 'utf-8', expected)

        # BOM is stripped when it agrees with the encoding, or used to
        # determine encoding
        bom_utf8_str = codecs.BOM_UTF8 + 'hi'
        self._assert_encoding(bom_utf8_str, 'utf-8', 'utf-8', u"hi")
        self._assert_encoding(bom_utf8_str, None, 'utf-8', u"hi")

    def test_utf16_32(self):
        # tools.ietf.org/html/rfc2781 section 4.3

        # USE BOM and strip it
        bom_be_str = codecs.BOM_UTF16_BE + u"hi".encode('utf-16-be')
        self._assert_encoding(bom_be_str, 'utf-16', 'utf-16-be', u"hi")
        self._assert_encoding(bom_be_str, None, 'utf-16-be', u"hi")

        bom_le_str = codecs.BOM_UTF16_LE + u"hi".encode('utf-16-le')
        self._assert_encoding(bom_le_str, 'utf-16', 'utf-16-le', u"hi")
        self._assert_encoding(bom_le_str, None, 'utf-16-le', u"hi")

        bom_be_str = codecs.BOM_UTF32_BE + u"hi".encode('utf-32-be')
        self._assert_encoding(bom_be_str, 'utf-32', 'utf-32-be', u"hi")
        self._assert_encoding(bom_be_str, None, 'utf-32-be', u"hi")

        bom_le_str = codecs.BOM_UTF32_LE + u"hi".encode('utf-32-le')
        self._assert_encoding(bom_le_str, 'utf-32', 'utf-32-le', u"hi")
        self._assert_encoding(bom_le_str, None, 'utf-32-le', u"hi")

        # if there is no BOM, big endian should be chosen
        self._assert_encoding(u"hi".encode('utf-16-be'), 'utf-16', 'utf-16-be', u"hi")
        self._assert_encoding(u"hi".encode('utf-32-be'), 'utf-32', 'utf-32-be', u"hi")

    def _assert_encoding_detected(self, header_encoding, expected_encoding, body, **kwargs):
        encoding, body_unicode = get_unicode_from_response(
            MockResponse(body, header_encoding), **kwargs)
        self.assertTrue(isinstance(body_unicode, unicode))
        self.assertEqual(norm_encoding(encoding), norm_encoding(expected_encoding))

    def test_html_encoding(self):
        # extracting the encoding from raw html is tested elsewhere
        body = ('blah blah < meta http-equiv="Content-Type" '
                'content="text/html; charset=iso-8859-1"> other stuff')
        self._assert_encoding_detected(None, 'cp1252', body)

        # header encoding takes precedence
        self._assert_encoding_detected('utf-8', 'utf-8', body)
        # BOM encoding takes precedence
        self._assert_encoding_detected(None, 'utf-8', codecs.BOM_UTF8 + body)

    def test_autodetect(self):
        body = '<meta charset="utf-8">'
        # body encoding takes precedence
        self._assert_encoding_detected(None, 'utf-8', body,
                auto_detect=True)
        # if no other encoding, the auto detect encoding is used.
        self._assert_encoding_detected(None, 'ascii', "no encoding info",
                auto_detect=True)
        # test no autodetect library
        import crawlmi.utils.encoding
        old_chardet, crawlmi.utils.encoding.chardet = crawlmi.utils.encoding.chardet, None
        self._assert_encoding_detected(None, 'utf-8', "no encoding info",
                auto_detect=True)
        crawlmi.utils.encoding.chardet = old_chardet

    def test_locale_encoding(self):
        self._assert_encoding_detected(None, 'utf-8', "no encoding info",
                locale='fa')
        self._assert_encoding_detected(None, 'big5', "no encoding info",
                locale='zh-tw')
        self._assert_encoding_detected(None, 'windows-1252', "no encoding info",
                locale='unknown')

    def test_default_encoding(self):
        # if no other method available, the default encoding of utf-8 is used
        self._assert_encoding_detected(None, 'utf-8', "no encoding info")
        # this can be overridden
        self._assert_encoding_detected(None, 'ascii', "no encoding info",
                default='ascii')

    def test_empty_body(self):
        # if no other method available, the default encoding of utf-8 is used
        self._assert_encoding_detected(None, 'utf-8', "")
