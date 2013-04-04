from optparse import make_option

from crawlmi import log
from crawlmi.spiders import BaseSpider
from crawlmi.settings import Settings


class BaseCommand(object):
    '''Base class for writing crawlmi commands (named commands executed through
    command line `crawlmi command ...`.

    Several attributes affect behavior at various steps along the way:

    ``args``
        A string listing the arguments accepted by the command,
        suitable for use in help messages; e.g., a command which takes
        a list of application names might set this to '<appname
        appname ...>'.

    ``requires_project``
        A boolean indicating whether the command needs to be able to
        import crawlmi settings; if ``True``, ``execute()`` will verify
        that this is possible before proceeding. Default value is
        ``False``.

    ``help``
        A short description of the command, which will be printed in
        help messages.

    ``option_list``
        This is the list of ``optparse`` options which will be fed
        into the command's ``OptionParser`` for parsing arguments.
    '''

    option_list = (
        make_option('--logfile', metavar='FILE', help='log file. if omitted stderr will be used'),
        make_option('-L', '--loglevel', metavar='LEVEL', default=log.INFO, help='log level (default: INFO)'),
        make_option('--nolog', action='store_true', help='disable logging completely'),
        make_option('-s', '--set', action='append', default=[], metavar='NAME=VALUE', help='set/override setting (may be repeated)'),
    )
    args = ''
    help = ''

    requires_project = False

    def set_engine(self, engine):
        self.engine = engine

    def get_settings(self):
        return Settings()

    def get_spider(self):
        return BaseSpider('')

    def handle(self, *args, **options):
        '''The actual logic of the command. Subclasses must implement this
        method.
        '''
        raise NotImplementedError()
