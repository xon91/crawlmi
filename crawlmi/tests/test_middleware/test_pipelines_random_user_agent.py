from twisted.trial import unittest

from crawlmi.exceptions import NotConfigured
from crawlmi.http import Request
from crawlmi.middleware.pipelines.random_user_agent import RandomUserAgent
from crawlmi.utils.test import get_engine


class RandomUserAgentTest(unittest.TestCase):
    def test_not_configured(self):
        engine = get_engine(RANDOM_USER_AGENT_LIST=[])
        self.assertRaises(NotConfigured, RandomUserAgent, engine)

    def test_process_request(self):
        engine = get_engine(RANDOM_USER_AGENT_LIST=['a'])
        mw = RandomUserAgent(engine)
        request = Request('http://github.com/')
        request = mw.process_request(request)
        self.assertEqual(request.headers['User-Agent'], 'a')

        # user agent shouldn't overwrite existing value
        engine = get_engine(RANDOM_USER_AGENT_LIST=['b'])
        mw = RandomUserAgent(engine)
        request = mw.process_request(request)
        self.assertEqual(request.headers['User-Agent'], 'a')
