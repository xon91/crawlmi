from twisted.internet import reactor


class LoopingCall(object):
    '''Schedule the periodic call of the function.
    '''

    def __init__(self, func, *args, **kwargs):
        # clock override is used in unittests
        self.clock = kwargs.pop('clock', None) or reactor

        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.delay = 0
        self._call = None
        self._remain_calls = None

    def schedule(self, delay=0, count=None, now=False):
        #assert countcount > 0, 'Number of calls for LoopingCall has to be positive!'
        self.cancel()

        self.delay = delay
        self._remain_calls = count
        if now:
            self._call = self.clock.callLater(0, self)
        else:
            self._call = self.clock.callLater(self.delay, self)

    def cancel(self):
        if self._call:
            self._call.cancel()
            self._call = None

    def calls_left(self):
        '''Return the number of calls left.
        Note: in a case of infinite loop, returns None.
        '''
        return self._remain_calls

    def is_scheduled(self):
        return self._call is not None

    def get_time(self):
        '''Return the time for which is this function scheduled.'''
        if self._call:
            return self._call.getTime()
        else:
            return 0

    def __call__(self):
        self._call = None
        if self._remain_calls is not None:
            self._remain_calls -= 1
            if self._remain_calls <= 0:
                self.cancel()
            else:
                self._call = self.clock.callLater(self.delay, self)
        else:
            self._call = self.clock.callLater(self.delay, self)
        self.func(*self.args, **self.kwargs)


class ScheduledCall(object):
    '''Schedule the function call for the future.
    Also ensure, that the function can be scheduled only once at a time.
    '''

    def __init__(self, func, *default_args, **default_kwargs):
        '''When scheduling the function, use `default_args` and
        `default_kwargs`, when no arguments are given to `schedule` function.
        '''

        # clock override is used in unittests
        self.clock = default_kwargs.pop('clock', None) or reactor

        self.func = func
        self.default_args = default_args
        self.default_kwargs = default_kwargs
        self._next_args = None
        self._next_kwargs = None
        self._call = None

    def schedule(self, delay=0, *args, **kwargs):
        '''Schedule the function call.
        `args` and `kwargs` overwrite `default_args` and `default_kwargs` if
        ANY of them is given.
        Return True, if the schedule was successfull.
        '''

        if self._call is None:
            if args or kwargs:
                self._next_args = args
                self._next_kwargs = kwargs
            else:
                self._next_args = self.default_args
                self._next_kwargs = self.default_kwargs

            self._call = self.clock.callLater(delay, self)
            return True
        return False

    def cancel(self):
        if self._call:
            self._call.cancel()
            self._call = None
            self._next_args = None
            self._next_kwargs = None

    def is_scheduled(self):
        return self._call is not None

    def get_time(self):
        '''Return the time for which is this function scheduled.'''
        if self._call:
            return self._call.getTime()
        else:
            return 0

    def __call__(self):
        # order of the following operations is very important in a case
        # when self.func schedules itself
        self._call = None
        args, self._next_args = self._next_args, None
        kwargs, self._next_kwargs = self._next_kwargs, None
        self.func(*args, **kwargs)
