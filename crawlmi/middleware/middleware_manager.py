from crawlmi import log
from crawlmi.exceptions import NotConfigured
from crawlmi.utils.misc import load_object


class MiddlewareManager(object):
    '''Base class for implementing middleware managers.'''

    # used in output messages
    component_name = ''

    def __init__(self, engine):
        self.engine = engine
        self.settings = engine.settings
        self.middlewares = self._get_middlewares()

    def _get_mwlist(self):
        raise NotImplementedError

    def _get_middlewares(self):
        mwlist = self._get_mwlist()
        middlewares = []
        for clspath in mwlist:
            try:
                mwcls = load_object(clspath)
                mw = mwcls(self.engine)
                middlewares.append(mw)
            except NotConfigured as e:
                clsname = clspath.split('.')[-1]
                log.msg(format='Disabled %(clsname)s: %(error)s',
                        level=log.WARNING, clsname=clsname, error=e)

        enabled = [x.__class__.__name__ for x in middlewares]
        log.msg(format='Enabled %(componentname)ss: %(enabledlist)s',
                level=log.DEBUG,
                componentname=self.component_name,
                enabledlist=', '.join(enabled))
        return middlewares
