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

class RequestDropped(Exception):
    '''Raised when pipeline processing drops the request.'''
    quiet = True


class RestartPipeline(Exception):
    '''Indicates that the pipeline processing should be restarted with the
    new value.
    '''
    def __init__(self, new_value):
        self.new_value = new_value
