import os
import re
import string

from crawlmi.utils.python import cut_suffix


def render_templatefile(path, **kwargs):
    with open(path, 'rb') as file:
        raw = file.read()

    content = string.Template(raw).substitute(**kwargs)

    with open(cut_suffix(path, '.tmpl'), 'wb') as file:
        file.write(content)
    if path.endswith('.tmpl'):
        os.remove(path)


_camelcase_invalid_chars_re = re.compile('[^a-zA-Z\d]')

def string_camelcase(string):
    '''Convert a word  to its CamelCase version and remove invalid chars.
    '''
    return _camelcase_invalid_chars_re.sub('', string.title())
