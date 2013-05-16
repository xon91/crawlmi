import inspect
import optparse
import os
import sys

import crawlmi
from crawlmi.commands.base import BaseCommand
from crawlmi.core.engine import Engine
from crawlmi.core.project import Project
from crawlmi.exceptions import UsageError
from crawlmi.settings import EngineSettings
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


def get_commands_from_module(module_path, inside_project):
    '''From the root module path (e.g. `crawlmi.commands`), find and return
    the dictionary (command_name -> command_class) of all the commands
    compatible with `inside_project` argument.
    '''
    commands = {}
    for cmd in iter_command_classes(module_path):
        if inside_project or not cmd.requires_project:
            cmd_name = cmd.__module__.split('.')[-1]
            commands[cmd_name] = cmd
    return commands


def get_commands(settings, inside_project):
    '''From the settings object, find and return the dictionary
    (command_name -> command_class) of all the commands compatible with
    `inside_project` argument.
    '''
    commands = get_commands_from_module('crawlmi.commands', inside_project)
    for module_path in settings.get_list('COMMAND_MODULES'):
        user_commands = get_commands_from_module(module_path, inside_project)
        commands.update(user_commands)
    return commands


def print_header(inside_project):
    if inside_project:
        print 'Crawlmi %s\n' % (crawlmi.__version__)
    else:
        print 'Crawlmi %s - no active project\n' % (crawlmi.__version__)


def print_commands(commands, inside_project):
    print_header(inside_project)
    print 'Usage:'
    print '  crawlmi <command> [options] [args]'
    print
    print 'Available commands:'
    for cmd_name, cmd_class in sorted(commands.iteritems()):
        print '  %-13s %s' % (cmd_name, cmd_class().short_desc())
    if not inside_project:
        print
        print 'More commands when inside the project...'
    print
    print 'Use "crawlmi <command> -h" to see more info about a command.'


def print_unknown_command(cmd_name, inside_project):
    print_header(inside_project)
    print 'Unknown command: %s\n' % cmd_name
    print 'Use "crawlmi" to see available commands'


def run_print_help(parser, func, *a, **kw):
    try:
        return func(*a, **kw)
    except UsageError as e:
        if str(e):
            parser.error(str(e))
        if e.print_help:
            parser.print_help()
        sys.exit(2)


def pop_command_name(argv):
    i = 0
    for arg in argv[1:]:
        if not arg.startswith('-'):
            del argv[i]
            return arg
        i += 1


def execute(argv=None):
    if argv is None:
        argv = sys.argv

    project = Project()
    settings = EngineSettings(module_settings=project.module_settings)
    inside_project = project.inside_project
    cmds = get_commands(settings, inside_project)
    cmd_name = pop_command_name(argv)
    if not cmd_name:
        print_commands(cmds, inside_project)
        sys.exit(0)
    elif cmd_name not in cmds:
        print_unknown_command(cmd_name, inside_project)
        sys.exit(2)

    # initialize the command
    cmd = cmds[cmd_name]()
    # initalize parser
    parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(),
                                   conflict_handler='resolve')
    parser.usage = 'crawlmi %s %s' % (cmd_name, cmd.syntax())
    parser.description = cmd.short_desc()
    cmd.add_options(parser)
    options, args = parser.parse_args(args=argv[1:])
    # initialize custom settings
    custom_settings = run_print_help(parser, cmd.get_settings, args, options)
    settings.custom_settings = custom_settings
    # initialize engine
    engine = Engine(settings, project, command_invoked=cmd_name)
    cmd.set_engine(engine)
    spider = run_print_help(parser, cmd.get_spider, args, options)
    engine.set_spider(spider)
    engine.setup()
    # save pidfile
    if getattr(options, 'pidfile', None):
        with open(options.pidfile, 'wb') as f:
            f.write(str(os.getpid()) + os.linesep)
    # run command
    run_print_help(parser, cmd.run, args, options)


if __name__ == '__main__':
    execute()
