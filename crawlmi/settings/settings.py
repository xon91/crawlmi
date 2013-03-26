class Settings(object):
    '''Settings is a dictionary-like data structure with some additional
    conveninent get methods for data conversions.
    '''

    @classmethod
    def from_module(cls, module_or_path):
        '''Initialize Settings() object from the module or the module path.
        Take all the module variables which name doesn't start with underscore.
        '''
        if isinstance(module_or_path, basestring):
            module_or_path = __import__(module_or_path, {}, {}, [''])
        args = filter(lambda x: not x.startswith('_'), dir(module_or_path))
        return cls(dict((k, getattr(module_or_path, k)) for k in args))

    def __init__(self, values=None):
        if values is None:
            values = {}
        self.values = values.copy()

    def __getitem__(self, name):
        return self.values[name]

    def __contains__(self, name):
        return name in self.values

    def get(self, name, default=None):
        return self.values.get(name, default)

    def __copy__(self):
        return self.__class__(self.values)
    copy = __copy__

    def get_bool(self, name, default=False):
        '''
        True is: 1, '1', True
        False is: 0, '0', False, None
        '''
        value = self.get(name, default)
        if value is None:
            return False
        return bool(int(value))

    def get_int(self, name, default=0):
        return int(self.get(name, default))

    def get_float(self, name, default=0.0):
        return float(self.get(name, default))

    def get_list(self, name, default=None):
        value = self.get(name)
        if value is None:
            return default if default is not None else []
        elif hasattr(value, '__iter__'):
            return value
        else:
            return str(value).split(',')
