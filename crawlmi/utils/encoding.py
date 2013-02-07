'''More info on encoding detection: http://www.whatwg.org/specs/web-apps/current-work/multipage/parsing.html
'''

import cgi
import codecs
import encodings
import re

from crawlmi.compat import chardet


# regexps for parsing HTTP meta tags
_template_pattern = r'''%s\s*=\s*["']?\s*%s\s*["']?'''
_httpequiv_re = _template_pattern % ('http-equiv', 'Content-Type')
_content_re = _template_pattern % ('content', r'(?P<mime>[^;]+);\s*charset=(?P<charset>[\w-]+)')
_content2_re = _template_pattern % ('charset', r'(?P<charset2>[\w-]+)')
_xml_encoding_re = _template_pattern % ('encoding', r'(?P<xmlcharset>[\w-]+)')

# check for meta tags, or xml decl. and stop search if a body tag is encountered
_body_encoding_re = re.compile(
    r'<\s*(?:meta(?:(?:\s+%s|\s+%s){2}|\s+%s)|\?xml\s[^>]+%s|body)' %
        (_httpequiv_re, _content_re, _content2_re, _xml_encoding_re), re.I)

def get_encoding_from_content(content):
    '''Supposing the content is either html or xml document, try to extract
    encoding from its contents.
    '''
    chunk = content[:2048]
    match = _body_encoding_re.search(chunk)
    if match:
        return _norm_encoding(match.group('charset') or
                match.group('charset2') or match.group('xmlcharset'))


def get_encoding_from_headers(headers):
    '''Returns encodings from given HTTP header.
    '''
    content_type = headers.get('content-type')
    if not content_type:
        return None
    content_type, params = cgi.parse_header(content_type)

    if 'charset' in params:
        encoding = params['charset'].strip("'\"")
    elif 'text' in content_type:
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html
        encoding = 'iso-8859-1'
    return _norm_encoding(encoding)


# map some encodings to the supersets, for faster and more robust resolution
_default_encoding_translation = {
    'ascii': 'cp1252',
    'euc_kr': 'cp949',
    'gb2312': 'gb18030',
    'gb_2312_80': 'gb18030',
    'gbk': 'gb18030',
    'iso8859_11': 'cp874',
    'iso8859_9': 'cp1254',
    'latin_1': 'cp1252',
    'macintosh': 'mac_roman',
    'shift_jis': 'cp932',
    'tis_620': 'cp874',
    'win_1251': 'cp1251',
    'windows_31j': 'cp932',
    'win_31j': 'cp932',
    'windows_874': 'cp874',
    'win_874': 'cp874',
    'x_sjis': 'cp932',
    'zh_cn': 'gb18030'
}

def _norm_encoding(encoding):
    '''Return the normalize form of the encoding.
    '''
    if not encoding:
        return encoding
    encoding = encodings.normalize_encoding(encoding).lower()
    encoding = encodings.aliases.aliases.get(encoding, encoding)
    encoding = _default_encoding_translation.get(encoding, encoding)
    try:
        return codecs.lookup(encoding).name
    except LookupError:
        return None


_bom_table = [
    (codecs.BOM_UTF32_BE, 'utf-32-be'),
    (codecs.BOM_UTF32_LE, 'utf-32-le'),
    (codecs.BOM_UTF16_BE, 'utf-16-be'),
    (codecs.BOM_UTF16_LE, 'utf-16-le'),
    (codecs.BOM_UTF8, 'utf-8'),
]
_first_chars = frozenset(c[0] for (c, _) in _bom_table)

def _read_bom(content):
    '''Read the byte order mark in the text, if present, and
    return the encoding represented by the BOM and the BOM.

    If no BOM can be detected, (None, None) is returned.
    '''
    # common case is no BOM, so this is fast
    if content and content[0] in _first_chars:
        for bom, encoding in _bom_table:
            if content.startswith(bom):
                return encoding, bom
    return None, None


_locale_mapping = {
    'ar': 'utf-8',
    'be': 'iso-8859-5',
    'bg': 'windows-1251',
    'cs': 'iso-8859-2',
    'cy': 'utf-8',
    'fa': 'utf-8',
    'he': 'windows-1255',
    'hr': 'utf-8',
    'hu': 'iso-8859-2',
    'ja': 'windows-31j',
    'kk': 'utf-8',
    'ko': 'windows-949',
    'ku': 'windows-1254',
    'lt': 'windows-1257',
    'lv': 'iso-8859-13',
    'mk': 'utf-8',
    'or': 'utf-8',
    'pl': 'iso-8859-2',
    'ro': 'utf-8',
    'ru': 'windows-1251',
    'sk': 'windows-1250',
    'sl': 'iso-8859-2',
    'sr': 'utf-8',
    'th': 'windows-874',
    'tr': 'windows-1254',
    'uk': 'windows-1251',
    'vi': 'utf-8',
    'zh-cn': 'gb18030',
    'zh-tw': 'big5',
}

def get_encoding_from_locale(locale):
    return _locale_mapping.get(locale, 'windows-1252')


def get_unicode_from_response(r, default='utf-8', locale=None, auto_detect=False):
    '''Return the unicode content from the response.

    This function tries to simulate the browser:
        1. http content type header
        2. BOM (byte-order mark)
        3. meta or xml tag declarations
        4. auto detection, if `auto_detect` is True
        5. locale specific, if `locale` is not None
        6. `default`

    If a BOM is found matching the encoding, it will be stripped.

    TODO: use the same encoding for the same domain!

    Returns a tuple of (encoding used, unicode)
    '''
    content = r.body

    enc = get_encoding_from_headers(r.headers)
    bom_enc, bom = _read_bom(content)
    if enc is not None:
        # remove BOM if it agrees with the encoding
        if enc == bom_enc:
            content = content[len(bom):]
        elif enc == 'utf-16' or enc == 'utf-32':
            # read endianness from BOM, or default to big endian
            # tools.ietf.org/html/rfc2781 section 4.3
            if bom_enc is not None and bom_enc.startswith(enc):
                enc = bom_enc
                content = content[len(bom):]
            else:
                enc += '-be'
        return enc, unicode(content, enc, 'replace')
    if bom_enc is not None:
        return bom_enc, unicode(content[len(bom):], bom_enc, 'replace')

    enc = get_encoding_from_content(content)
    if enc is None and chardet is not None and auto_detect:
        enc = chardet.detect(content)['encoding']
    if enc is None and locale:
        enc = get_encoding_from_locale(locale)
    if enc is None:
        enc = default
    return enc, unicode(content, enc, 'replace')
