from operator import itemgetter
from pprint import pformat

from crawlmi.commands.base import BaseCommand
from crawlmi.utils.python import cut_suffix


class Command(BaseCommand):
    requires_project = False
    command_settings = {'LOG_ENABLED': False}

    def syntax(self):
        return '[options]'

    def short_desc(self):
        return 'Get settings values.'

    def add_options(self, parser):
        parser.add_option('--get', dest='get', metavar='SETTING',
            help='print raw setting value')
        parser.add_option('--getbool', dest='getbool', metavar='SETTING',
            help='print setting value, intepreted as a boolean')
        parser.add_option('--getint', dest='getint', metavar='SETTING',
            help='print setting value, intepreted as an integer')
        parser.add_option('--getfloat', dest='getfloat', metavar='SETTING',
            help='print setting value, intepreted as an float')
        parser.add_option('--getlist', dest='getlist', metavar='SETTING',
            help='print setting value, intepreted as an float')
        parser.add_option('--spider', dest='spider',
            help='use this spider\'s settings')

    def run(self, args, options):
        settings = self.engine.settings
        if options.get:
            print settings.get(options.get)
        elif options.getbool:
            print settings.get_bool(options.getbool)
        elif options.getint:
            print settings.get_int(options.getint)
        elif options.getfloat:
            print settings.get_float(options.getfloat)
        elif options.getlist:
            print settings.get_list(options.getlist)
        else:
            special_dicts = ['PIPELINE', 'EXTENSIONS']
            for key in sorted(settings.keys()):
                if key in special_dicts:
                    d = settings.get(key + '_BASE')
                    d.update(settings.get(key))
                    value = [(k, v) for k, v in sorted(d.items(), key=itemgetter(1))
                             if v is not None]
                elif cut_suffix(key, '_BASE') in special_dicts:
                    continue
                else:
                    value = settings.get(key)
                print '%s: %s' % (key, pformat(value))
