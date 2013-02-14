import unittest2

from crawlmi.utils.clock import Clock
from crawlmi.utils.defer import ScheduledCall, LoopingCall


class ModifiedObject(object):
    def __init__(self):
        self.num_calls = 0
        self.args = None
        self.kwargs = None

    def func(self, *args, **kwargs):
        self.num_calls += 1
        self.args = args
        self.kwargs = kwargs


class ScheduledCallTest(unittest2.TestCase):
    default_args = (10, 'hello')
    default_kwargs = {'a': 47, 'b': 'c'}

    def setUp(self):
        self.clock = Clock()
        self.obj = ModifiedObject()
        self.sc = ScheduledCall(self.obj.func, clock=self.clock,
                                *self.default_args,
                                **self.default_kwargs)

    def _check(self, args, kwargs):
        if args is None:
            self.assertIsNone(self.obj.args)
        else:
            self.assertTupleEqual(self.obj.args, args)

        if kwargs is None:
            self.assertIsNone(self.obj.kwargs)
        else:
            self.assertEqual(self.obj.kwargs, kwargs)

    def test_init(self):
        # test initializing ScheduledCall without overriding its clock
        sc = ScheduledCall(self.obj.func, *self.default_args,
                           **self.default_kwargs)
        sc.schedule()
        sc.cancel()

    def test_get_time_and_is_scheduled(self):
        self.clock.advance(10)

        self.assertFalse(self.sc.is_scheduled())
        self.assertEqual(self.sc.get_time(), 0)
        self.sc.schedule(5)
        self.assertTrue(self.sc.is_scheduled())
        self.assertEqual(self.sc.get_time(), 15)
        self.clock.advance(5)
        self.assertFalse(self.sc.is_scheduled())
        self.assertEqual(self.sc.get_time(), 0)

    def test_no_delay(self):
        self.sc.schedule()
        self._check(None, None)
        self.clock.advance(0)
        self._check(self.default_args, self.default_kwargs)

    def test_default(self):
        self.assertTrue(self.sc.schedule(5))
        self._check(None, None)
        self.clock.advance(1)
        self.assertFalse(self.sc.schedule(1))
        self.clock.advance(2)
        self._check(None, None)
        self.clock.advance(3)
        self._check(self.default_args, self.default_kwargs)

    def test_cancel(self):
        self.sc.schedule(5)
        self.clock.advance(3)
        self.sc.cancel()
        self.clock.advance(3)
        self._check(None, None)
        self.assertTrue(self.sc.schedule(1))
        self.clock.advance(1)
        self._check(self.default_args, self.default_kwargs)

    def test_overwrite(self):
        over_args = ('crawlmi',)
        over_kwargs = {'a': 50, 'd': 'e'}
        self.sc.schedule(5, *over_args, **over_kwargs)
        self.clock.advance(5)
        self._check(over_args, over_kwargs)

    def test_partial_overwrite(self):
        over_args = ('crawlmi',)
        self.sc.schedule(5, *over_args)
        self.clock.advance(5)
        self._check(over_args, {})

    def test_nested_schedule(self):
        def func(*args, **kwargs):
            self.obj.func(*args, **kwargs)
            self.sc.schedule()
        self.sc.func = func
        self.sc.schedule()
        self.assertEqual(self.obj.num_calls, 0)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 1)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 2)

    def test_nested_schedule_delay(self):
        args1 = ('a',)
        kwargs1 = {'a': 'b'}
        args2 = ('b',)
        kwargs2 = {'b': 'c'}

        def func(*args, **kwargs):
            self.obj.func(*args, **kwargs)
            self.sc.schedule(4, *args2, **kwargs2)
        self.sc.func = func
        self.sc.schedule(3, *args1, **kwargs1)
        self.clock.advance(3)
        self.assertIsNotNone(self.sc._call)
        self._check(args1, kwargs1)
        self.clock.advance(3)
        self._check(args1, kwargs1)
        self.clock.advance(1)
        self._check(args2, kwargs2)


class LoopingCallTest(unittest2.TestCase):
    default_args = (10, 'hello')
    default_kwargs = {'a': 47, 'b': 'c'}

    def setUp(self):
        self.clock = Clock()
        self.obj = ModifiedObject()
        self.sc = LoopingCall(self.obj.func, clock=self.clock,
                              *self.default_args,
                              **self.default_kwargs)

    def _check(self, args, kwargs):
        if args is None:
            self.assertIsNone(self.obj.args)
        else:
            self.assertTupleEqual(self.obj.args, args)

        if kwargs is None:
            self.assertIsNone(self.obj.kwargs)
        else:
            self.assertEqual(self.obj.kwargs, kwargs)

    def test_init(self):
        # test initializing LoopingCall without overriding its clock
        sc = LoopingCall(self.obj.func, *self.default_args,
                           **self.default_kwargs)
        sc.schedule()
        sc.cancel()

    def test_basic(self):
        # scheduling
        self.assertFalse(self.sc.is_scheduled())
        self.sc.schedule(2, count=2, now=False)
        # before the first call
        self.assertTrue(self.sc.is_scheduled())
        self.assertEqual(self.sc.get_time(), 2)
        self.assertEqual(self.sc.calls_left(), 2)
        self.clock.advance(1)
        self.assertEqual(self.obj.num_calls, 0)
        # after the first call
        self.clock.advance(1)
        self.assertEqual(self.obj.num_calls, 1)
        self.assertEqual(self.sc.calls_left(), 1)
        self._check(self.default_args, self.default_kwargs)
        # after the second call
        self.clock.advance(2)
        self.assertEqual(self.obj.num_calls, 2)
        self.assertEqual(self.sc.calls_left(), 0)
        self.assertFalse(self.sc.is_scheduled())
        # no more calls
        self.clock.advance(20)
        self.assertEqual(self.obj.num_calls, 2)

    def test_now(self):
        self.sc.schedule(2, count=2, now=True)
        self.assertEqual(self.obj.num_calls, 0)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 1)
        self.clock.advance(20)
        self.assertEqual(self.obj.num_calls, 2)

    def test_infinite(self):
        self.sc.schedule(2)
        self.clock.pump([2] * 100)
        self.assertEqual(self.obj.num_calls, 100)
        self.assertTrue(self.sc.is_scheduled())
        self.assertIsNone(self.sc.calls_left())

    def test_cancel(self):
        self.sc.schedule(2)
        self.clock.advance(1)
        self.sc.cancel()
        self.clock.advance(20)
        self.assertEqual(self.obj.num_calls, 0)

    def test_reschedule(self):
        self.sc.schedule(2)
        self.clock.advance(1)
        self.sc.schedule(5)
        self.clock.advance(4)
        self.assertEqual(self.obj.num_calls, 0)
        self.clock.advance(1)
        self.assertEqual(self.obj.num_calls, 1)

    def test_no_delay(self):
        self.sc.schedule()
        self.assertEqual(self.obj.num_calls, 0)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 1)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 2)

    def test_nested_schedule(self):
        def func(*args, **kwargs):
            self.obj.func(*args, **kwargs)
            self.sc.schedule()
        self.sc.func = func
        self.sc.schedule()
        self.assertEqual(self.obj.num_calls, 0)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 1)
        self.clock.advance(0)
        self.assertEqual(self.obj.num_calls, 2)
