'''Core exceptions.'''

# Internal

class NotConfigured(Exception):
    '''Indicates a missing configuration situation.'''
    pass

class NotSupported(Exception):
    '''Indicates a feature or method is not supported.'''
    pass
