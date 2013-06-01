import inspect
from pkgutil import iter_modules


def arg_to_iter(arg):
    '''Convert an argument to an iterable. The argument can be a None, single
    value, or an iterable.

    Exception: if arg is a dict, [arg] will be returned
    '''
    if arg is None:
        return []
    elif not isinstance(arg, dict) and hasattr(arg, '__iter__'):
        return arg
    else:
        return [arg]


def load_object(path):
    '''Load an object given its absolute object path, and return it.

    object can be a class, function, variable or instance.
    '''

    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError('Error loading object `%s`: not a full path' % path)

    module, name = path[:dot], path[dot+1:]
    try:
        mod = __import__(module, {}, {}, [''])
    except ImportError as e:
        raise ImportError('Error loading object `%s`: %s' % (path, e))

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError('Module `%s` doesn\'t define any object named `%s`' %
                        (module, name))
    return obj


def iter_submodules(module_path):
    '''Loads a module and all its submodules from a the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.

    For example: iter_submodules('crawlmi.utils')
    '''

    mods = []
    mod = __import__(module_path, {}, {}, [''])
    mods.append(mod)
    if hasattr(mod, '__path__'):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = module_path + '.' + subpath
            if ispkg:
                mods += iter_submodules(fullpath)
            else:
                submod = __import__(fullpath, {}, {}, [''])
                mods.append(submod)
    return mods


def iter_subclasses(module_path, base_class, include_base=False):
    '''Iterate through submodules of the `module_path` and return all the
    classes that are subclasses of the `base_class`.

    If `include_base` is False, `base_class` is not returned.
    '''
    for module in iter_submodules(module_path):
        for obj in vars(module).itervalues():
            if (inspect.isclass(obj) and
                    issubclass(obj, base_class) and
                    obj.__module__ == module.__name__ and
                    (include_base or obj is not base_class)):
                yield obj
