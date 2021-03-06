import os

tests_dir = os.path.dirname(os.path.abspath(__file__))
tests_datadir = os.path.join(tests_dir, 'sample_data')


def get_testdata(*paths):
    '''Return test data'''
    path = os.path.join(tests_datadir, *paths)
    with open(path, 'rb') as f:
        result = f.read()
    return result
