from threading import Thread

from crawlmi.commands.base import BaseCommand
from crawlmi.exceptions import UsageError
from crawlmi.shell import Shell


class Command(BaseCommand):
    requires_project = False
    command_settings = {
        'LOG_STATS_INTERVAL': 0,
        'STATS_DUMP': False,
    }

    def syntax(self):
        return '[url|file]'

    def short_desc(self):
        return 'Interactive console for given url.'

    def add_options(self, parser):
        BaseCommand.add_options(self, parser)

    def update_vars(self, vars):
        '''You can use this function to update the Crawlmi objects that will be
        available in the shell.
        Return the list of object names to print in the `shelp()`.
        '''

    def run(self, args, options):
        if len(args) > 1:
            raise UsageError()

        url = args[0] if args else None
        shell = Shell(self.engine, update_vars=self.update_vars)
        self._start_shell_thread(shell, url)
        self.process.start()

    def _start_shell_thread(self, shell, url):
        t = Thread(target=shell.start, kwargs={'url': url})
        t.daemon = True
        t.start()
