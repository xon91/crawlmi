from collections import defaultdict
from functools import partial

from crawlmi.parser.quantity import Quantity
from crawlmi.utils.python import get_func_args


def wrap_context(function, context):
    if 'context' in get_func_args(function):
        return partial(function, context=context)
    else:
        return function


class SValidationError(Exception):
    '''Raised, when the page doesn't validate with the S object.'''


class S(object):
    '''Class S is an efficient to select multiple, possibly nested, parts of
    the website, automatically validate their existence/quantity and parse them
    out.

    Parsed values are stored in a dictionary as result[S.name] = [parsed_items]
    Parsed values are either xpath nodes or unicode strings if S.value is used.
    '''

    def __init__(self, name, xpath, quant='*', value=None, callback=None, group=None, children=None):
        '''
        name - the parsed item will be stored in a dictionary on this index (not to store the item, use '_' as a prefix of the name).
        xpath - xpath to the item.
        quant - used for validation. The expected number of items to be parsed.
        value - specify it, if you want the items to be extracted. Otherwise selector objects will be returned.
        callback - callback function to be called on each found item. It can take named argument "context", which is dictionary containing additionnal values.
        group - if not None, all the child nodes will be stored under one dictionary entry of group's name
        children - list of nested S objects. For each item found, each child will be called with the item as the selector.
        '''
        self.name = name
        self.xpath = xpath
        self.quant = Quantity(quant)
        self.value = value
        self.callback = callback
        self.group = group
        self.children = children if children is not None else []

    @property
    def visible(self):
        return self.name and not self.name.startswith('_')

    def parse(self, selector, context=None):
        result = defaultdict(list)
        items = selector.select(self.xpath)
        num_items = len(items)
        if not self.quant.check_quantity(num_items):
            raise SValidationError(
                'Number of selected `%s` items %s doesn\'t match the expected quant %s.' %
                (self.name, num_items, self.quant.raw_quant))

        for item in items:
            if self.visible:
                if self.value is not None:
                    extracted = item.select(self.value).extract()
                    if self.callback is not None:
                        context_callback = wrap_context(self.callback, context)
                        try:
                            extracted = map(context_callback, extracted)
                        except Exception as e:
                            raise SValidationError(
                                'Callback function returned an error on item `%s`: %s' %
                                (self.name, e))
                    result[self.name].extend(extracted)
                else:
                    if self.callback is not None:
                        context_callback = wrap_context(self.callback, context)
                        try:
                            item = context_callback(item)
                        except Exception as e:
                            raise SValidationError(
                                'Callback function returned an error on item `%s`: %s' %
                                (self.name, e))
                    result[self.name].append(item)

            if self.group is not None:
                groupd = defaultdict(list)
                for c in self.children:
                    for k, v in c.parse(item, context).iteritems():
                        groupd[k].extend(v)
                result[self.group].append(groupd)
            else:
                for c in self.children:
                    for k, v in c.parse(item, context).iteritems():
                        result[k].extend(v)
        return result

    def xpath_exists(self, selector):
        return len(selector.select(self.xpath)) >= 1

    def add_child(self, child):
        self.children.append(child)

    @property
    def all_fields(self):
        result = {}
        if self.visible:
            result[self.name] = None

        children_fields = {}
        for c in self.children:
            children_fields.update(c.all_fields)
        if self.group is not None:
            result[self.group] = children_fields
        else:
            result.update(children_fields)
        return result
