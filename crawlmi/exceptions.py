'''Core exceptions.'''


# Internal

class NotConfigured(Exception):
    '''Indicates a missing configuration situation.'''
    pass


class NotSupported(Exception):
    '''Indicates a feature or method is not supported.'''
    pass


# Commands

class UsageError(Exception):
    '''To indicate a command-line usage error.'''
    def __init__(self, *a, **kw):
        self.print_help = kw.pop('print_help', True)
        super(UsageError, self).__init__(*a, **kw)


# Downloader pipeline

class DropRequest(Exception):
    '''Raised when pipeline processing drops the request.'''
    quiet = True


class RestartPipeline(Exception):
    '''Indicates that the pipeline processing should be restarted with the
    new value.
    '''
    def __init__(self, new_value):
        self.new_value = new_value


# Spider

class DontStopEngine(Exception):
    '''Don't stop the engine, even when it is idle.
    Raised from `spider_idle` signal handlers.
    '''
    pass


class StopEngine(Exception):
    '''Request the engine to stop.
    Raised from Request's callback functions.
    '''
    def __init__(self, reason='cancelled'):
        self.reason = reason
