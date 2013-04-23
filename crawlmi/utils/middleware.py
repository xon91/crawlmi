import re


_first_cap_re = re.compile(r'(.)([A-Z][a-z]+)')
_all_cap_re = re.compile(r'([a-z0-9])([A-Z])')

def camelcase_to_capital(string):
    '''Converts cammel case string into all capitals with underscores.
    E.g.: CamelCase -> CAMEL_CASE
    '''
    string = _first_cap_re.sub(r'\1_\2', string)
    return _all_cap_re.sub(r'\1_\2', string).upper()
