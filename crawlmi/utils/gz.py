from cStringIO import StringIO
from gzip import GzipFile
import struct

from crawlmi.exceptions import DecompressSizeError


def gunzip(data, max_length=0):
    '''Gunzip the given data and return as much data as possible.
    This is resilient to CRC checksum errors.
    '''
    f = GzipFile(fileobj=StringIO(data))
    output = ''
    chunk = '.'
    while chunk:
        try:
            chunk = f.read(8196)
            output += chunk
            if max_length and len(output) > max_length:
                raise DecompressSizeError('Object exceeded %s bytes' %
                                          max_length)
        except (IOError, EOFError, struct.error):
            # complete only if there is some data, otherwise re-raise
            # see issue 87 about catching struct.error
            # some pages are quite small so output is '' and f.extrabuf
            # contains the whole page content
            if output or f.extrabuf:
                output += f.extrabuf
                break
            else:
                raise
    return output


def is_gzipped(response):
    '''Return True if the response is gzipped, or False otherwise'''
    ctype = response.headers.get('Content-Type', '')
    return ctype in ('application/x-gzip', 'application/gzip')
