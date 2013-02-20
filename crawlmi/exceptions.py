'''Core exceptions.'''

# Internal

class NotConfigured(Exception):
    '''Indicates a missing configuration situation.'''
    pass

class NotSupported(Exception):
    '''Indicates a feature or method is not supported.'''
    pass


# Downloader pipeline

class RestartPipeline(Exception):
    '''Indicates that the pipeline processing should be restarted with the
    new value.
    '''
    def __init__(self, new_value):
        self.new_value = new_value
