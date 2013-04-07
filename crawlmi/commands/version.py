import platform
import sys

import twisted

import crawlmi
from crawlmi.commands.base import BaseCommand


class Command(BaseCommand):
    requires_project = False
    command_settings = {'LOG_ENABLED': False}

    def syntax(self):
        return '[-v]'

    def short_desc(self):
        return 'Print Crawlmi version'

    def add_options(self, parser):
        parser.add_option('--verbose', '-v', dest='verbose', action='store_true',
            help='also display twisted/python/platform info (useful for bug reports)')

    def run(self, args, options):
        if options.verbose:
            try:
                import lxml.etree
            except ImportError:
                lxml_version = libxml2_version = '(lxml not available)'
            else:
                lxml_version = '.'.join(map(str, lxml.etree.LXML_VERSION))
                libxml2_version = '.'.join(map(str, lxml.etree.LIBXML_VERSION))
            print 'Crawlmi  : %s' % crawlmi.__version__
            print 'lxml    : %s' % lxml_version
            print 'libxml2 : %s' % libxml2_version
            print 'Twisted : %s' % twisted.version.short()
            print 'Python  : %s' % sys.version.replace('\n', '- ')
            print 'Platform: %s' % platform.platform()
        else:
            print 'Crawlmi %s' % crawlmi.__version__
