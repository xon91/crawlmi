from twisted.trial import unittest

from crawlmi.middleware.pipelines.chunked_transfer import ChunkedTransfer
from crawlmi.utils.test import get_engine


class ChunkedTransferTest(unittest.TestCase):
    def test_decode_chunked_transfer(self):
        ct = ChunkedTransfer(get_engine())

        chunked_body = '25\r\n' + 'This is the data in the first chunk\r\n\r\n'
        chunked_body += '1C\r\n' + 'and this is the second one\r\n\r\n'
        chunked_body += '3\r\n' + 'con\r\n'
        chunked_body += '8\r\n' + 'sequence\r\n'
        chunked_body += '0\r\n\r\n'
        body = ct._decode_chunked_transfer(chunked_body)
        self.assertEqual(body, \
            'This is the data in the first chunk\r\n' +
            'and this is the second one\r\n' +
            'consequence')
