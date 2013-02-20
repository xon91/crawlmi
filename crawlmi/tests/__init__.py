import os


tests_datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_data')


def get_testdata(*paths):
    '''Return test data'''
    path = os.path.join(tests_datadir, *paths)
    return open(path, 'rb').read()
