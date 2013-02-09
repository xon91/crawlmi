class Settings(object):
    def __init__(self, values={}):
        self.values = values.copy()

    def __getitem__(self, key):
        return self.values[key]

    def __contains__(self, key):
        return key in self.values

    def get(self, name, default=None):
        return self.values.get(name, default)

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
