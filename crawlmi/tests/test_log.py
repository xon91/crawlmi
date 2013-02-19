from twisted.python import log as txlog, failure
from twisted.trial import unittest

from crawlmi import log
from crawlmi.utils.test import LogWrapper


class CrawlmiFileLogObserverTest(unittest.TestCase):
    def setUp(self):
        self.lw = LogWrapper()
        self.lw.setUp(log.INFO, 'utf-8')

    def tearDown(self):
        self.flushLoggedErrors()
        self.lw.tearDown()

    def test_msg_basic(self):
        log.msg('Hello')
        self.assertEqual(self.lw.get_logged(), '[crawlmi] INFO: Hello')

    def test_msg_level1(self):
        log.msg('Hello', level=log.WARNING)
        self.assertEqual(self.lw.get_logged(), '[crawlmi] WARNING: Hello')

    def test_msg_level2(self):
        log.msg('Hello', log.WARNING)
        self.assertEqual(self.lw.get_logged(), '[crawlmi] WARNING: Hello')

    def test_msg_wrong_level(self):
        log.msg('Hello', level=9999)
        self.assertEqual(self.lw.get_logged(), '[crawlmi] NOLEVEL: Hello')

    def test_msg_encoding(self):
        log.msg(u'Price: \xa3100')
        self.assertEqual(self.lw.get_logged(), '[crawlmi] INFO: Price: \xc2\xa3100')

    def test_msg_ignore_level(self):
        log.msg('Hello', level=log.DEBUG)
        log.msg('World', level=log.INFO)
        self.assertEqual(self.lw.get_logged(), '[crawlmi] INFO: World')

    def test_msg_ignore_system(self):
        txlog.msg('Hello')
        self.assertEqual(self.lw.get_logged(), '')

    def test_msg_ignore_system_err(self):
        txlog.err('Hello')
        self.assertEqual(self.lw.get_logged(), '[-] ERROR: \'Hello\'')

    def test_err_noargs(self):
        try:
            a = 1 / 0
        except:
            log.err()
        self.assertIn('Traceback', self.lw.get_logged())
        self.assertIn('ZeroDivisionError', self.lw.get_logged())

    def test_err_why(self):
        log.err(TypeError('bad type'), 'Wrong type')
        self.assertEqual(self.lw.get_first_line(), '[crawlmi] ERROR: Wrong type')
        self.assertIn('TypeError', self.lw.get_logged())
        self.assertIn('bad type', self.lw.get_logged())

    def test_error_outside_crawlmi(self):
        '''Crawlmi logger should still print outside errors'''
        txlog.err(TypeError('bad type'), 'Wrong type')
        self.assertEqual(self.lw.get_first_line(), '[-] ERROR: Wrong type')
        self.assertIn('TypeError', self.lw.get_logged())
        self.assertIn('bad type', self.lw.get_logged())

    # this test fails in twisted trial observer, not in crawlmi observer
    # def test_err_why_encoding(self):
    #     log.err(TypeError('bad type'), u'\xa3')
    #     self.assertEqual(self.lw.get_first_line(), '[crawlmi] ERROR: \xc2\xa3')

    def test_err_exc(self):
        log.err(TypeError('bad type'))
        self.assertIn('Unhandled Error', self.lw.get_logged())
        self.assertIn('TypeError', self.lw.get_logged())
        self.assertIn('bad type', self.lw.get_logged())

    def test_err_failure(self):
        log.err(failure.Failure(TypeError('bad type')))
        self.assertIn('Unhandled Error', self.lw.get_logged())
        self.assertIn('TypeError', self.lw.get_logged())
        self.assertIn('bad type', self.lw.get_logged())
