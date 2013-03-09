def to_unicode(value, encoding='utf-8', errors='strict'):
    if isinstance(value, unicode):
        return value
    elif isinstance(value, str):
        return value.decode(encoding, errors)
    else:
        return unicode(value)


def to_str(value, encoding='utf-8', errors='strict'):
    if isinstance(value, str):
        return value
    elif isinstance(value, unicode):
        return value.encode(encoding, errors)
    else:
        return str(value)


_binarychars = set(map(chr, xrange(32))) - set(['\0', '\t', '\n', '\r'])

def is_binary(data):
    '''Return True if the given data is considered binary, or False
    otherwise, by looking for binary bytes.
    '''
    return any(c in _binarychars for c in data)
