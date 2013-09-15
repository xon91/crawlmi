'''Imports of optional libraries.'''

optional_features = set()

try:
    import charade as chardet
except ImportError:
    try:
        import chardet
    except ImportError:
        chardet = None
if chardet is not None:
    optional_features.add('chardet')

try:
    import OpenSSL
except ImportError:
    OpenSSL = None
if OpenSSL is not None:
    optional_features.add('ssl')


try:
    import cssselect
except ImportError:
    cssselect = None
if cssselect is not None:
    optional_features.add('cssselect')
