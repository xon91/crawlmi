'''Imports of optional libraries.'''

try:
    import charade as chardet
except ImportError:
    try:
        import chardet
    except ImportError:
        chardet = None
