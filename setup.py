from os.path import dirname, join
from setuptools import setup, find_packages


with open(join(dirname(__file__), 'crawlmi/VERSION'), 'rb') as f:
    version = f.read().decode('ascii').strip()


setup(
    name='crawlmi',
    version=version,
    description='Highly optimized web scraping framework.',
    long_description=open('README.md', 'rb').read(),
    author='Michal "Mimino" Danilak',
    maintainer='Michal "Mimino" Danilak',
    maintainer_email='michal.danilak@gmail.com',
    url='https://github.com/Mimino666/crawlmi',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['crawlmi = crawlmi.cmdline:execute']
    },
    classifiers=[
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
    install_requires=[
        'charade',
        'cssselect>=0.9',
        'lxml',
        'PyDispatcher>=2.0.5',
        'pyOpenSSL',
        'Twisted>=13.1.0',
        'xextract',
    ]
)
