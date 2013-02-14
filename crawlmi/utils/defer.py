from twisted.internet import reactor


class ScheduledCall(object):
    '''Schedule the function call for the future.
    Also ensure, that the function can be scheduled only once at a time.
    '''

    def __init__(self, func, *default_args, **default_kwargs):
        '''When scheduling the function, use `default_args` and
        `default_kwargs`, when no arguments are given to `schedule` function.
        '''

        self._func = func
        self._default_args = default_args
        self._default_kwargs = default_kwargs
        self._next_args = None
        self._next_kwargs = None
        self._call = None
        # clock override is used in unittests
        self.clock = default_kwargs.pop('clock', None) or reactor

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
                self._next_args = self._default_args
                self._next_kwargs = self._default_kwargs

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
        # when self._func schedules itself
        self._call = None
        args, self._next_args = self._next_args, None
        kwargs, self._next_kwargs = self._next_kwargs, None
        result = self._func(*args, **kwargs)
        return result
