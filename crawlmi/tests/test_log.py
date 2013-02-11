from cStringIO import StringIO

from twisted.python import log as txlog, failure
from twisted.trial import unittest

from crawlmi import log


class CrawlmiFileLogObserverTest(unittest.TestCase):

    level = log.INFO
    encoding = 'utf-8'

    def setUp(self):
        self.f = StringIO()
        self.flo = log.CrawlmiFileLogObserver(self.f, self.level, self.encoding)
        self.flo.start()

    def tearDown(self):
        self.flushLoggedErrors()
        self.flo.stop()

    def logged(self):
        return self.f.getvalue().strip()[25:]  # strip timestamp

    def first_log_line(self):
        logged = self.logged()
        return logged.splitlines()[0] if logged else ''

    def test_msg_basic(self):
        log.msg('Hello')
        self.assertEqual(self.logged(), '[crawlmi] INFO: Hello')

    def test_msg_level1(self):
        log.msg('Hello', level=log.WARNING)
        self.assertEqual(self.logged(), '[crawlmi] WARNING: Hello')

    def test_msg_level2(self):
        log.msg('Hello', log.WARNING)
        self.assertEqual(self.logged(), '[crawlmi] WARNING: Hello')

    def test_msg_wrong_level(self):
        log.msg('Hello', level=9999)
        self.assertEqual(self.logged(), '[crawlmi] NOLEVEL: Hello')

    def test_msg_encoding(self):
        log.msg(u'Price: \xa3100')
        self.assertEqual(self.logged(), '[crawlmi] INFO: Price: \xc2\xa3100')

    def test_msg_ignore_level(self):
        log.msg('Hello', level=log.DEBUG)
        log.msg('World', level=log.INFO)
        self.assertEqual(self.logged(), '[crawlmi] INFO: World')

    def test_msg_ignore_system(self):
        txlog.msg('Hello')
        self.assertEqual(self.logged(), '')

    def test_msg_ignore_system_err(self):
        txlog.err('Hello')
        self.assertEqual(self.logged(), '[-] ERROR: \'Hello\'')

    def test_err_noargs(self):
        try:
            a = 1/0
        except:
            log.err()
        self.assertIn('Traceback', self.logged())
        self.assertIn('ZeroDivisionError', self.logged())

    def test_err_why(self):
        log.err(TypeError('bad type'), 'Wrong type')
        self.assertEqual(self.first_log_line(), '[crawlmi] ERROR: Wrong type')
        self.assertIn('TypeError', self.logged())
        self.assertIn('bad type', self.logged())

    def test_error_outside_scrapy(self):
        '''Scrapy logger should still print outside errors'''
        txlog.err(TypeError('bad type'), 'Wrong type')
        self.assertEqual(self.first_log_line(), '[-] ERROR: Wrong type')
        self.assertIn('TypeError', self.logged())
        self.assertIn('bad type', self.logged())

    # this test fails in twisted trial observer, not in crawlmi observer
    # def test_err_why_encoding(self):
    #     log.err(TypeError('bad type'), u'\xa3')
    #     self.assertEqual(self.first_log_line(), '[crawlmi] ERROR: \xc2\xa3')

    def test_err_exc(self):
        log.err(TypeError('bad type'))
        self.assertIn('Unhandled Error', self.logged())
        self.assertIn('TypeError', self.logged())
        self.assertIn('bad type', self.logged())

    def test_err_failure(self):
        log.err(failure.Failure(TypeError('bad type')))
        self.assertIn('Unhandled Error', self.logged())
        self.assertIn('TypeError', self.logged())
        self.assertIn('bad type', self.logged())
