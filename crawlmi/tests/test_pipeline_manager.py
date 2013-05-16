from twisted.python.failure import Failure
from twisted.trial import unittest

from crawlmi.exceptions import RestartPipeline, DropRequest
from crawlmi.http import Request, Response
from crawlmi.middleware.pipeline_manager import PipelineManager
from crawlmi.utils.test import get_engine


class PipelineManagerTest(unittest.TestCase):
    def setUp(self):
        self.mws = []
        self.actions = []
        self.req = Request('http://gh.com/')
        self.resp = Response('http://gh.com/', request=self.req)
        self.fail = Failure(Exception())
        self.fail.request = self.req

    def _build(self, name, preq=None, presp=None, pexc=None):
        funcs = {}
        if preq is not None:
            funcs['process_request'] = (lambda x: x) if preq == True else preq
        if presp is not None:
            funcs['process_response'] = (lambda x: x) if presp == True else presp
        if pexc is not None:
            funcs['process_failure'] = (lambda x: x) if pexc == True else pexc

        for k in funcs:
            old_f = funcs[k]
            def new_f(_self, x):
                self.mws.append(name)
                self.actions.append(k)
                return old_f(x)
            funcs[k] = new_f

        funcs['__init__'] = lambda _self, engine: None
        return type(name, (object,), funcs)

    def _get_pm(self, *mw_classes):
        return PipelineManager(get_engine(), mw_classes=mw_classes)

    def test_process_request_normal(self):
        pm = self._get_pm(
            self._build('M1'),
            self._build('M2', preq=True))
        result = pm.process_request(self.req)
        self.assertIs(result, self.req)
        self.assertListEqual(self.mws, ['M2'])

    def test_process_request_none(self):
        pm = self._get_pm(
            self._build('M1', preq=lambda x: None),
            self._build('M2', preq=True))
        self.assertRaises(DropRequest, pm.process_request, self.req)
        self.assertListEqual(self.mws, ['M1'])

    def test_process_request_response(self):
        pm = self._get_pm(
            self._build('M1', preq=lambda x: Response('')),
            self._build('M2', preq=True))
        result = pm.process_request(self.req)
        self.assertIsInstance(result, Response)
        self.assertListEqual(self.mws, ['M1'])

    def test_process_reqeust_restart(self):
        old_request = Request('http://gh.com/')
        new_request = Request('http://new.com/')

        def preq(r):
            if r is old_request:
                raise RestartPipeline(new_request)
            return r

        pm = self._get_pm(
            self._build('M1', preq=preq),
            self._build('M2', preq=True))
        result = pm.process_request(old_request)
        self.assertIs(result, new_request)
        self.assertListEqual(self.mws, ['M1', 'M1', 'M2'])

    def test_process_request_invalid(self):
        pm = self._get_pm(self._build('M1', preq=lambda x: 10))
        self.assertRaises(AssertionError, pm.process_request, self.req)

        def preq(r):
            raise RestartPipeline(Response(''))
        pm = self._get_pm(self._build('M1', preq=preq))
        self.assertRaises(AssertionError, pm.process_request, self.req)

        def preq2(r):
            raise ValueError
        pm = self._get_pm(self._build('M1', preq=preq2))
        self.assertRaises(ValueError, pm.process_request, self.req)

    # careful when testing process_response - middlewares are in reversed order

    def test_process_response_normal(self):
        pm = self._get_pm(
            self._build('M3', presp=True),
            self._build('M2', presp=True),
            self._build('M1'))
        result = pm.process_response(self.resp)
        self.assertIs(self.resp, result)
        self.assertListEqual(self.mws, ['M2', 'M3'])
        self.assertListEqual(self.actions, ['process_response', 'process_response'])

    def test_process_failure_normal(self):
        pm = self._get_pm(
            self._build('M2', pexc=True),
            self._build('M1'))
        result = pm.process_response(self.fail)
        self.assertIs(self.fail, result)
        self.assertListEqual(self.mws, ['M2'])
        self.assertListEqual(self.actions, ['process_failure'])

    def test_process_response_request(self):
        pm = self._get_pm(
            self._build('M2', presp=True),
            self._build('M1', presp=lambda x: self.req))
        result = pm.process_response(self.resp)
        self.assertIs(result, self.req)
        self.assertListEqual(self.mws, ['M1'])

    def test_process_response_none(self):
        pm = self._get_pm(
            self._build('M2', presp=True),
            self._build('M1', presp=lambda x: None))
        result = pm.process_response(self.resp)
        self.assertIsInstance(result, Failure)
        self.assertIsInstance(result.value, DropRequest)
        self.assertListEqual(self.mws, ['M1'])

    def test_process_response_to_failure(self):
        def presp(x):
            raise ValueError
        pm = self._get_pm(
            self._build('M2', pexc=True),
            self._build('M1', presp=presp))
        result = pm.process_response(self.resp)
        self.assertIsInstance(result, Failure)
        self.assertIsInstance(result.value, ValueError)
        self.assertListEqual(self.mws, ['M1', 'M2'])
        self.assertListEqual(self.actions, ['process_response', 'process_failure'])

    def test_process_failure_to_response(self):
        pm = self._get_pm(
            self._build('M2', presp=True),
            self._build('M1', pexc=lambda x: self.resp))
        result = pm.process_response(self.fail)
        self.assertIsInstance(result, Response)
        self.assertListEqual(self.mws, ['M1', 'M2'])
        self.assertListEqual(self.actions, ['process_failure', 'process_response'])

    def test_process_response_invalid(self):
        pm = self._get_pm(self._build('M1', presp=lambda x: 10))
        self.assertRaises(AssertionError, pm.process_response, self.resp)

    def test_enabled_setting(self):
        pm = self._get_pm(self._build('M1', preq=True, presp=True, pexc=True))
        self.req.meta['M1_ENABLED'] = False
        pm.process_request(self.req)
        pm.process_response(self.resp)
        pm.process_response(self.fail)
        self.assertListEqual(self.actions, [])
