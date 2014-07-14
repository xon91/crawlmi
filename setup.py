import os
import sys


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def is_not_module(filename):
    return os.path.splitext(filename)[1] not in ['.py', '.pyc', '.pyo']

for crawlmi_dir in ['crawlmi']:
    for dirpath, dirnames, filenames in os.walk(crawlmi_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'):
                del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
            data = [f for f in filenames if is_not_module(f)]
            if data:
                data_files.append([dirpath, [os.path.join(dirpath, f) for f in data]])
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# Small hack for working with bdist_wininst.
# See http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
if len(sys.argv) > 1 and sys.argv[1] == 'bdist_wininst':
    for file_info in data_files:
        file_info[0] = '\\PURELIB\\%s' % file_info[0]


scripts = ['bin/crawlmi']
if os.name == 'nt':
    scripts.append('bin/crawlmi.bat')

version = __import__('crawlmi').__version__

setup_args = {
    'name': 'crawlmi',
    'version': version,
    'description': 'Highly optimized web scraping framework.',
    'long_description': open('README.md', 'rb').read(),
    'author': 'Michal "Mimino" Danilak',
    'maintainer': 'Michal "Mimino" Danilak',
    'maintainer_email': 'michal.danilak@gmail.com',
    'url': 'https://github.com/Mimino666/crawlmi',
    'packages': packages,
    'data_files': data_files,
    'scripts': scripts,
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
    ],
}

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
else:
    setup_args['install_requires'] = [
        'Twisted>=13.0.0',
        'lxml',
        'pyOpenSSL',
        'charade',
        'cssselect>=0.9',
    ]

setup(**setup_args)
