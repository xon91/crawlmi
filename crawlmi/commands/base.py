from optparse import OptionGroup

from crawlmi import log
from crawlmi.core.process import Process
from crawlmi.exceptions import UsageError
from crawlmi.settings import Settings
from crawlmi.spider import BaseSpider
from crawlmi.utils.url import is_url


class BaseCommand(object):
    '''Base class for writing crawlmi commands - named commands executed
    through command line `crawlmi command ...`.

    Attributes:

    `requires_project`
        A boolean indicating whether the command needs to be able to
        import crawlmi settings; if `True`, `execute()` will verify
        that this is possible before proceeding. Default value is
        `False`.

    `command_settings`
        Command specific settings to be applied and override the project
        settings. By default, these settings are overriden through coommand
        line `-s` option.

    Process of initialization is:
        1. `get_settings()` is called to receive the command specific settings.
        2. `set_engine()` is called. Spider is still uninitialized.
        3. `get_spider()` is called.
        4. `handle()` is called. Engine is fully initialized. To start
           crawlnig process, call `self.process.start()`.
    '''

    requires_project = False
    command_settings = {}

    def syntax(self):
        '''Command syntax. Do not include command name. Don't use newlines.
        '''
        return ''

    def short_desc(self):
        '''A short description of the command. Don't use newlines.
        '''
        return ''

    def help(self):
        '''An extensive help for the command. It will be shown when using the
        `help` command. It can contain newlines, since not post-formatting will
        be applied to its contents.
        '''
        return self.short_desc()

    def add_options(self, parser):
        '''Populate option parse with options available for this command.
        '''
        group = OptionGroup(parser, "Global Options")
        group.add_option('--logfile', metavar='FILE', help='log file. if omitted stderr will be used')
        group.add_option('-L', '--loglevel', metavar='LEVEL', default=log.DEBUG, help='log level (default: DEBUG)')
        group.add_option('--nolog', action='store_true', help='disable logging completely')
        group.add_option('-s', '--set', action='append', default=[], metavar='NAME=VALUE', help='set/override setting (may be repeated)')
        group.add_option('--spider', dest='spider', help='use this spider')
        parser.add_option_group(group)

    def get_settings(self, args, options):
        '''Return command specific settings. Default behavior is to combine
        `command_settings` with the settings received from command line.

        `self.engine` is still not initialized, so don't use it.
        '''
        custom_settings = self.command_settings.copy()

        try:
            cmdline_settings = dict(x.split('=', 1) for x in options.set)
            custom_settings.update(cmdline_settings)
        except ValueError:
            raise UsageError('Invalid -s value, use -s NAME=VALUE',
                             print_help=False)

        # logging behavior
        if options.logfile:
            custom_settings['LOG_ENABLED'] = True
            custom_settings['LOG_FILE'] = options.logfile
        if options.loglevel:
            custom_settings['LOG_ENABLED'] = True
            custom_settings['LOG_LEVEL'] = options.loglevel
        if options.nolog:
            custom_settings['LOG_ENABLED'] = False

        return Settings(custom_settings)

    def set_engine(self, engine):
        self.engine = engine
        self.settings = engine.settings
        self.process = Process(engine)

    def get_spider(self, args, options):
        spiders = self.engine.spiders
        if options.spider:
            return spiders.create_spider_by_name(options.spider)
        if len(args) == 1 and is_url(args[0]):
            spider = spiders.create_spider_by_url(args[0])
            if spider:
                return spider
        return BaseSpider('')

    def handle(self, args, options):
        '''The actual logic of the command. Subclasses must implement this
        method.
        '''
        raise NotImplementedError()
