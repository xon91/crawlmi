from crawlmi import log
from crawlmi.exceptions import NotConfigured
from crawlmi.utils.middleware import camelcase_to_capital
from crawlmi.utils.misc import load_object


class MiddlewareManager(object):
    '''Base class for implementing middleware managers.'''

    # used in output messages
    component_name = ''

    def __init__(self, engine, mw_classes=None):
        self.engine = engine
        self.settings = engine.settings
        self.middlewares = self._get_middlewares(mw_classes)

    def _get_mwlist(self):
        raise NotImplementedError

    def _get_middlewares(self, mw_classes):
        if mw_classes is None:
            mwlist = []
            for clspath in self._get_mwlist():
                mwlist.append(load_object(clspath))
        else:
            mwlist = mw_classes

        self.mwlist = mwlist
        middlewares = []
        for mwcls in mwlist:
            try:
                # middlewares disabled through enabled_setting
                if hasattr(mwcls, 'enabled_setting'):
                    enabled_setting = mwcls.enabled_setting
                else:
                    enabled_setting = ('%s_ENABLED' %
                                       camelcase_to_capital(mwcls.__name__))
                if not self.settings.get_bool(enabled_setting, True):
                    raise NotConfigured()

                mw = mwcls(self.engine)
                mw.enabled_setting = enabled_setting
                middlewares.append(mw)
            except NotConfigured as e:
                log.msg(format='Disabled %(clsname)s: %(error)s',
                        level=log.WARNING, clsname=mwcls, error=e)

        enabled = [x.__class__.__name__ for x in middlewares]
        log.msg(format='Enabled %(componentname)ss: %(enabledlist)s',
                level=log.DEBUG,
                componentname=self.component_name,
                enabledlist=', '.join(enabled))
        return middlewares
