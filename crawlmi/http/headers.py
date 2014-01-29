from crawlmi.utils.python import to_str


class Headers(dict):

    def __init__(self, seq=None, encoding='utf-8'):
        self.encoding = encoding
        if seq is not None:
            self.update(seq)

    def normkey(self, key):
        return to_str(key.title(), self.encoding)

    def normvalue(self, value):
        if not hasattr(value, '__iter__'):
            value = [value]
        return [to_str(x, self.encoding) for x in value]

    def __getitem__(self, key):
        return dict.__getitem__(self, self.normkey(key))[-1]

    def __setitem__(self, key, value):
        dict.__setitem__(self, self.normkey(key), self.normvalue(value))

    def __delitem__(self, key):
        dict.__delitem__(self, self.normkey(key))

    def __contains__(self, key):
        return dict.__contains__(self, self.normkey(key))
    has_key = __contains__

    def __copy__(self):
        return self.__class__(self, self.encoding)
    copy = __copy__

    def setdefault(self, key, default=None):
        return dict.setdefault(self, self.normkey(key), self.normvalue(default))

    def get(self, key, default=None):
        key = self.normkey(key)
        return self[key] if key in self else default

    def getlist(self, key, default=None):
        key = self.normkey(key)
        if key in self:
            return dict.__getitem__(self, key)
        else:
            if default is None:
                default = []
            if not hasattr(default, '__iter__'):
                default = [default]
            return default

    def appendlist(self, key, value):
        lst = self.getlist(key)
        lst.extend(self.normvalue(value))
        self[key] = lst

    def add(self, key, value):
        key = self.normkey(key)
        value = self.normvalue(value)
        if key not in self:
            dict.__setitem__(self, key, value)
        else:
            dict.__getitem__(self, key).extend(value)

    def update(self, seq):
        seq = seq.iteritems() if isinstance(seq, dict) else seq
        for (k, v) in seq:
            self.add(k, v)

    def values(self):
        return [self[k] for k in self.keys()]

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        return ((k, self.getlist(k)) for k in self.keys())

    def to_string(self):
        '''Returns a raw HTTP headers representation of headers.
        '''
        raw_lines = []
        for key, value in self.iteritems():
            if isinstance(value, (str, unicode)):
                raw_lines.append('%s: %s' % (key, value))
            elif isinstance(value, (list, tuple)):
                for v in value:
                    raw_lines.append('%s: %s' % (key, v))
        return '\r\n'.join(raw_lines)
