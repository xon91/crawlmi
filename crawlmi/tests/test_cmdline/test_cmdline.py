from twisted.trial import unittest

from crawlmi.cmdline import (iter_command_classes, get_commands_from_module,
                             get_commands)
from crawlmi.settings import Settings
from crawlmi.tests.test_cmdline.sample_commands.command1 import TestCommand1


class CmdlineTest(unittest.TestCase):
    def test_iter_command_classes(self):
        commands = set(
            x.__name__ for x in
            iter_command_classes('crawlmi.tests.test_cmdline.sample_commands'))
        self.assertSetEqual(commands, set(['TestCommand1', 'TestCommand2']))

        # BaseCommand should not be included
        base_commands = set(
            x.__name__ for x in
            iter_command_classes('crawlmi.commands'))
        self.assertNotIn('BaseCommand', base_commands)

    def test_get_commands_from_module(self):
        commands = get_commands_from_module('crawlmi.tests.test_cmdline.sample_commands', True)
        self.assertSetEqual(set(commands.keys()), set(['command1', 'command2']))
        self.assertIs(commands['command1'], TestCommand1)

        commands = get_commands_from_module('crawlmi.tests.test_cmdline.sample_commands', False)
        self.assertSetEqual(set(commands.keys()), set(['command2']))

    def test_get_commands(self):
        settings = Settings({'COMMANDS_MODULE': 'crawlmi.tests.test_cmdline.sample_commands'})
        commands = get_commands(settings, False)
        self.assertNotIn('command1', commands)
        self.assertIn('command2', commands)
