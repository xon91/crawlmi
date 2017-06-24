from ConfigParser import SafeConfigParser
from importlib import import_module
import os
import sys
import warnings

from crawlmi.settings import Settings


class Project(object):
    '''Project provides the project-specific information.

    To initialize a dummy project pass `path=None`.
    '''

    def __init__(self, path='.'):
        self.inside_project = False
        self.cfg_path = self.get_closest_cfg(path=path)
        self.cfg = None
        self.project_dir = None
        self.module_settings = Settings()  # user-defined settings file
        self._data_dir = None

        if self.cfg_path:
            # init project dir
            self.project_dir = os.path.dirname(self.cfg_path)
            if self.project_dir not in sys.path:
                sys.path.append(self.project_dir)
            # init cfg
            self.cfg = SafeConfigParser()
            self.cfg.read([self.cfg_path])
            # init settings
            if self.cfg.has_option('crawlmi', 'settings'):
                settings_module_path = self.cfg.get('crawlmi', 'settings')
                try:
                    settings_module = import_module(settings_module_path)
                except ImportError as exc:
                    warnings.warn(
                        'Cannot import crawlmi settings module %s: %s' %
                        (settings_module_path, exc))
                else:
                    self.module_settings = Settings.from_module(settings_module)
                    self.inside_project = True

    def set_data_dir(self, data_dir):
        if data_dir is None:
            self._data_dir = None
        else:
            self._data_dir = os.path.join(self.project_dir, data_dir)

    @property
    def data_dir(self):
        return self._data_dir if self._data_dir else '.crawlmi'

    def data_path(self, path, create_dir=False):
        '''If path is relative, return the given path inside the project data
        dir, otherwise return the path unmodified.
        '''
        if not os.path.isabs(path):
            path = os.path.join(self.data_dir, path)
        if create_dir and not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_closest_cfg(self, path, prev_path=None):
        '''Return the path to the closest crawlmi.cfg file by traversing the current
        directory and its parents.
        '''
        if path == prev_path:
            return
        path = os.path.abspath(path)
        cfgfile = os.path.join(path, 'crawlmi.cfg')
        if os.path.exists(cfgfile):
            return os.path.abspath(cfgfile)
        return self.get_closest_cfg(os.path.dirname(path), path)
