from cStringIO import StringIO
from gzip import GzipFile
import re
import struct

import six

from crawlmi.exceptions import DecompressSizeError


# - Python>=3.5 GzipFile's read() has issues returning leftover
#   uncompressed data when input is corrupted
#   (regression or bug-fix compared to Python 3.4)
# - read1(), which fetches data before raising EOFError on next call
#   works here but is only available from Python>=3.3
# - scrapy does not support Python 3.2
# - Python 2.7 GzipFile works fine with standard read() + extrabuf
if six.PY2:
    def read1(gzf, size=-1):
        return gzf.read(size)
else:
    def read1(gzf, size=-1):
        return gzf.read1(size)


def gunzip(data, max_length=0):
    '''Gunzip the given data and return as much data as possible.
    This is resilient to CRC checksum errors.
    '''
    f = GzipFile(fileobj=StringIO(data))
    output = ''
    chunk = '.'
    while chunk:
        try:
            chunk = read1(f, 8196)
            output += chunk
            if max_length and len(output) > max_length:
                raise DecompressSizeError('Object exceeded %s bytes' % max_length)
        except (IOError, EOFError, struct.error):
            # complete only if there is some data, otherwise re-raise
            # see issue 87 about catching struct.error
            # some pages are quite small so output is '' and f.extrabuf
            # contains the whole page content
            if output or getattr(f, 'extrabuf', None):
                try:
                    output += f.extrabuf[-f.extrasize:]
                finally:
                    break
            else:
                raise
    return output


_is_gzipped = re.compile(br'^application/(x-)?gzip\b', re.I).search
_is_octetstream = re.compile(br'^(application|binary)/octet-stream\b', re.I).search

def is_gzipped(response):
    '''Return True if the response is gzipped, or False otherwise.'''
    ctype = response.headers.get('Content-Type', b'')
    cenc = response.headers.get('Content-Encoding', b'').lower()
    return (_is_gzipped(ctype) or
            (_is_octetstream(ctype) and cenc in (b'gzip', b'x-gzip')))


def gzip_magic_number(response):
    return response.body[:3] == '\x1f\x8b\x08'
