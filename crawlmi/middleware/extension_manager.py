from crawlmi.middleware.middleware_manager import MiddlewareManager
from crawlmi.utils.conf import build_component_list


class ExtensionManager(MiddlewareManager):
    component_name = 'extension'

    def __init__(self, *args, **kwargs):
        super(ExtensionManager, self).__init__(*args, **kwargs)
        self.extensions = {}
        for mw in self.middlewares:
            if hasattr(mw, 'name'):
                self.extensions[mw.name] = mw

    def _get_mwlist(self):
        return build_component_list(self.settings['EXTENSIONS_BASE'],
                                    self.settings['EXTENSIONS'])

    def __getitem__(self, key):
        return self.extensions[key]
