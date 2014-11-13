from setuptools import setup, find_packages
version = version = __import__('crawlmi').__version__

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
        'Twisted>=13.0.0',
        'lxml',
        'pyOpenSSL',
        'charade',
        'cssselect>=0.9',
    ]
)
