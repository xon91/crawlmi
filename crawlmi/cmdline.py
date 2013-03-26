import inspect

from crawlmi.commands.base import BaseCommand
from crawlmi.utils.misc import iter_submodules


def iter_command_classes(module_path):
    '''From the root module path (e.g. `crawlmi.commands`), iterate through all
    the submodules and load and return all the command classes.
    '''
    for module in iter_submodules(module_path):
        for obj in vars(module).itervalues():
            if (inspect.isclass(obj) and
                    obj is not BaseCommand and
                    issubclass(obj, BaseCommand) and
                    obj.__module__ == module.__name__):
                yield obj


def get_commands_from_module(module_path, inproject):
    '''From the root module path (e.g. `crawlmi.commands`), find and return
    the dictionary (command_name -> command_obj) of all the commands compatible
    with `inproject` argument.
    '''
    commands = {}
    for cmd in iter_command_classes(module_path):
        if inproject or not cmd.requires_project:
            cmd_name = cmd.__module__.split('.')[-1]
            commands[cmd_name] = cmd()
    return commands


def get_commands(settings, inproject):
    '''From the settings object, find and return the dictionary
    (command_name -> command_obj) of all the commands compatible with
    `inproject` argument.
    '''
    commands = get_commands_from_module('crawlmi.commands', inproject)
    module_path = settings.get('COMMANDS_MODULE')
    if module_path:
        user_commands = get_commands_from_module(module_path, inproject)
        commands.update(user_commands)
    return commands
