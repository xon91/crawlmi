import os
import re
import shutil
from shutil import copytree, ignore_patterns
import string
import sys

import crawlmi
from crawlmi.commands.base import BaseCommand
from crawlmi.exceptions import UsageError
from crawlmi.utils.template import render_templatefile, string_camelcase


_templates_path = os.path.join(crawlmi.__path__[0], 'templates', 'project')

_templates_to_render = (
    ('crawlmi.cfg',),
    ('${project_name}', 'settings.py.tmpl'),
)

_ignore = ignore_patterns('*.pyc')


class Command(BaseCommand):
    requires_project = False
    command_settings = {'LOG_ENABLED': False}

    def syntax(self):
        return '<project_name>'

    def short_desc(self):
        return 'Create new project'

    def add_options(self, parser):
        pass

    def run(self, args, options):
        if len(args) != 1:
            raise UsageError()
        project_name = args[0]
        if not re.search(r'^[_a-zA-Z]\w*$', project_name):
            print ('Error: Project names must begin with a letter and contain '
                   'only letters, numbers and underscores')
            sys.exit(1)
        elif os.path.exists(project_name):
            print 'Error: directory %r already exists' % project_name
            sys.exit(1)

        module_tmpl = os.path.join(_templates_path, 'module')
        copytree(module_tmpl, os.path.join(project_name, project_name), ignore=_ignore)
        shutil.copy(os.path.join(_templates_path, 'crawlmi.cfg'), project_name)
        for paths in _templates_to_render:
            path = os.path.join(*paths)
            file_tmpl = os.path.join(
                project_name,
                string.Template(path).substitute(project_name=project_name))
            render_templatefile(
                file_tmpl,
                project_name=project_name,
                ProjectName=string_camelcase(project_name))
