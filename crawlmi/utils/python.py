import inspect
import re


def to_unicode(value, encoding=None, errors='strict'):
    if encoding is None:
        encoding = 'utf-8'
    if isinstance(value, unicode):
        return value
    elif isinstance(value, str):
        return value.decode(encoding, errors)
    else:
        return unicode(value)


def to_str(value, encoding=None, errors='strict'):
    if encoding is None:
        encoding = 'utf-8'
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


def get_func_args(func, stripself=False):
    '''Return the argument name list of a callable.'''
    if inspect.isfunction(func):
        func_args, _, _, _ = inspect.getargspec(func)
    elif inspect.isclass(func):
        return get_func_args(func.__init__, True)
    elif inspect.ismethod(func):
        return get_func_args(func.__func__, True)
    elif inspect.ismethoddescriptor(func):
        return []
    elif hasattr(func, '__call__'):
        if inspect.isroutine(func):
            return []
        else:
            return get_func_args(func.__call__, True)
    else:
        raise TypeError('%s is not callable' % type(func))
    if stripself:
        func_args.pop(0)
    return func_args


def flatten(x):
    '''flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).
    '''
    result = []
    for el in x:
        if hasattr(el, '__iter__'):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def unique_list(list_, key=lambda x: x):
    '''Efficient function to uniquify a list preserving item order.
    '''
    seen = {}
    result = []
    for item in list_:
        seenkey = key(item)
        if seenkey in seen:
            continue
        seen[seenkey] = 1
        result.append(item)
    return result


_re_type = type(re.compile(''))

def regex(x):
    return x if isinstance(x, _re_type) else re.compile(x)
