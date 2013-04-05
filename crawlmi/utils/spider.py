import inspect

from crawlmi.spider import BaseSpider


def iter_spider_classes(module):
    '''Return an iterator over all spider classes defined in the given module
    that can be instantiated (i.e. which have a name).
    '''
    for obj in vars(module).itervalues():
        if (inspect.isclass(obj) and
                issubclass(obj, BaseSpider) and
                obj.__module__ == module.__name__ and
                getattr(obj, 'name', None)):
            yield obj
