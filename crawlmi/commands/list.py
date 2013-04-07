from crawlmi.commands.base import BaseCommand


class Command(BaseCommand):
    requires_project = True
    command_settings = {'LOG_ENABLED': False}

    def short_desc(self):
        return 'List available spiders'

    def add_options(self, parser):
        pass

    def run(self, args, options):
        for sp_name in self.engine.spiders.get_spiders():
            print sp_name
