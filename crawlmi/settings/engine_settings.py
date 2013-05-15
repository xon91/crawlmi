from crawlmi.settings.settings import Settings


class EngineSettings(Settings):
    def __init__(self, default_settings=None, module_settings=None,
                 spider_settings=None, custom_settings=None):
        if default_settings is None:
            default_settings = Settings.from_module(
                'crawlmi.settings.default_settings')
        super(EngineSettings, self).__init__(default_settings)
        self.module_settings = Settings(module_settings)
        self.spider_settings = Settings(spider_settings)
        self.custom_settings = Settings(custom_settings)

        self.order = ['custom_settings', 'spider_settings', 'module_settings',
                      'values']

    def __getitem__(self, name):
        for settings_name in self.order:
            settings = getattr(self, settings_name)
            if name in settings:
                return settings[name]
        raise KeyError(name)

    def __contains__(self, name):
        for settings_name in self.order:
            settings = getattr(self, settings_name)
            if name in settings:
                return True
        return False

    def keys(self):
        keys = set()
        for settings_name in self.order:
            settings = getattr(self, settings_name)
            keys.update(settings.keys())
        return list(keys)

    def get(self, name, default=None):
        for settings_name in self.order:
            settings = getattr(self, settings_name)
            if name in settings:
                return settings[name]
        return default
