from crawlmi.http import Response
from crawlmi.parser.selectors import XPathSelector


class SP(object):
    '''Class SP is used to process the results from class S into a user
    friendly form.
    '''

    def __init__(self, s=None, **kwargs):
        self.s = s
        self.filters = kwargs
        if s is not None:
            self.validate(s)

    def parse(self, parsed, context=None):
        # convenience parsing directly out of response of selector classes
        if isinstance(parsed, (Response, XPathSelector)):
            if self.s is None:
                raise TypeError('To parse directly from response or selector, you need to specify S class, first.')
            return self.parse(self.s.parse(parsed, context))

        result = {}
        for k, v in self.filters.iteritems():
            if isinstance(v, SP):
                children = []
                for child in parsed.get(k, []):
                    children.append(v.parse(child))
                result[k] = children
            else:
                result[k] = v(parsed, k)
        return result

    def validate(self, s):
        '''Check whether every field defined in the current SP object is also
        defined in S object.
        Raises ValueError if some field from SP is not defind is S.
        Returns the dictionary of redundant fields in S.
        '''
        missing = self._validate_fields(s.all_fields)
        return missing

    def _validate_fields(self, fields):
        for k, v in self.filters.iteritems():
            if isinstance(v, SP):
                if isinstance(fields.get(k), dict):
                    v._validate_fields(fields[k])
                else:
                    raise ValueError(
                        'Expected nested structure for field name `%s`.' % k)
            elif k not in fields:
                raise ValueError('Undefined field name `%s`.' % k)
            if not fields[k]:
                del fields[k]
        return fields

    ###########################################################################
    # Filters (they CANNOT change `parsed`)
    ###########################################################################

    @staticmethod
    def id(parsed, key):
        '''Return the value just as it is stored.
        Return None, if value does not exist.
        '''
        return parsed.get(key)

    class _joiner(object):
        '''Return the joined values with the given separator.
        Return empty string, if value does not exist.
        '''
        def __init__(self, sep, normalize=True):
            '''
            If normalize is True, strip the parsed results before joining them
            and also discard empty results after stripping.
            '''
            self.sep = sep
            self.normalize = normalize

        def __call__(self, parsed, key):
            vals = parsed.get(key, [])
            if self.normalize:
                vals = [v.strip() for v in vals if v and not v.isspace()]
            return self.sep.join(vals)

    one = _joiner('')
    space = _joiner(' ')
    comma = _joiner(',')

    @staticmethod
    def unique(parsed, key):
        return list(set(parsed.get(key, [])))

    ###########################################################################
    # Filter factories (their names end with "f")
    ###########################################################################

    @staticmethod
    def joinf(sep, normalize=True):
        def f(parsed, key):
            vals = parsed.get(key, [])
            if normalize:
                vals = [v.strip() for v in vals if v and not v.isspace()]
            return sep.join(vals)
        return f

    @staticmethod
    def defaultf(default):
        '''Use the given default value if the parsed value is not present.'''
        def f(parsed, key):
            return parsed.get(key, default)
        return f

    @staticmethod
    def applyf(func):
        '''Apply the given function on the parsed value.'''
        def f(parsed, key):
            return func(parsed.get(key, None))
        return f

    @staticmethod
    def composef(*filters):
        '''Apply the many filters in the given order.
        To each filter, the whole parsed dictionary is always passed
        '''
        if not filters:
            raise ValueError(
                'At least one filter has to be passed to `compose` filter.')
        def f(parsed, key):
            is_present = key in parsed
            original = parsed.get(key)

            for f in filters:
                parsed[key] = f(parsed, key)
            result = parsed[key]
            if is_present:
                parsed[key] = original
            else:
                del parsed[key]
            return result
        return f
