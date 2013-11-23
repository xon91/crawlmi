from collections import defaultdict
import urlparse

from crawlmi.compat import optional_features
from crawlmi.parser.quantity import Quantity
from crawlmi.utils.python import get_func_args

css_supported = 'cssselect' in optional_features
if css_supported:
    from cssselect import GenericTranslator


class SValidationError(Exception):
    '''Raised, when the page doesn't validate with the S object.'''


class S(object):
    '''Class S is an efficient to select multiple, possibly nested, parts of
    the website, automatically validate their existence/quantity and parse them
    out.

    Parsed values are stored in a dictionary as result[S.name] = [parsed_items]
    Parsed values are either xpath nodes or unicode strings if S.value is used.
    '''

    def __init__(self, name, xpath=None, quant='*', value=None, callback=None,
                 group=None, children=None, css=None, filter=None):
        '''
        name - the parsed item will be stored in a dictionary on this index (not to store the item, use '_' as a prefix of the name).
        xpath - xpath to the item.
        quant - used for validation. The expected number of items to be parsed.
        value - specify it, if you want the items to be extracted. Otherwise selector objects will be returned.
        callback - callback function to be called on each found item. It can take named argument "context", which is dictionary containing additionnal values.
        group - if not None, all the child nodes will be stored under one dictionary entry of group's name
        children - list of nested S objects. For each item found, each child will be called with the item as the selector.
        css - css selector, in a case xpath is not defined
        filter - one-argument function. Given the node from the xpath, return true, if to the node. Otherwise return False.
                 `quant` is checked AFTER the filter is applied.
        '''
        if (xpath is None) == (css is None):
            raise TypeError('Exactly one of `xpath` or `css` arguments must be specified.')

        self.name = name
        if xpath is not None:
            self.raw_xpath = xpath
        elif css_supported:
            self.raw_xpath = GenericTranslator().css_to_xpath(css)
        else:
            raise TypeError('Css selectors not supported, install cssselect library.')
        self.hashed_namespaces = None
        self.compiled_xpath = None
        self.quant = Quantity(quant)
        self.raw_value = value
        self.compiled_value = None
        self.callback = callback
        self.context_callback = callback and 'context' in get_func_args(callback)
        self.group = group
        self.children = children if children is not None else []
        self.filter = filter

    def get_nodes(self, name):
        '''Return the list of S nodes with the given name.'''
        result = []
        if self.name == name:
            result.append(self)
        for c in self.children:
            result += c.get_nodes(name)
        return result

    @property
    def visible(self):
        return self.name and not self.name.startswith('_')

    def _hash_namespaces(self, namespaces):
        return hash(frozenset(namespaces.iteritems())) if namespaces else 0

    def parse(self, response_or_selector, context=None):
        from crawlmi.http import HtmlResponse, XmlResponse
        if isinstance(response_or_selector, (HtmlResponse, XmlResponse)):
            context = context or {}
            context['response'] = response_or_selector
            selector = response_or_selector.selector
        else:
            selector = response_or_selector
        return self._parse(selector, context)

    def _parse(self, selector, context):
        hashed_namespaces = self._hash_namespaces(selector.namespaces)
        if self.compiled_xpath is None or self.hashed_namespaces != hashed_namespaces:
            self.hashed_namespaces = hashed_namespaces
            self.compiled_xpath = selector.compile_xpath(self.raw_xpath)
            if self.raw_value is not None:
                self.compiled_value = selector.compile_xpath(self.raw_value)

        result = defaultdict(list)
        nodes = selector.select(self.compiled_xpath)
        original_num_nodes = len(nodes)
        if self.filter:
            nodes = filter(self.filter, nodes)
        filtered_num_nodes = len(nodes)
        if not self.quant.check_quantity(filtered_num_nodes):
            if self.filter:
                raise SValidationError(
                    'Number of `%s` nodes %s (%s before filtering) doesn\'t match the expected quant %s.' %
                    (self.name, filtered_num_nodes, original_num_nodes, self.quant.raw_quant))
            else:
                raise SValidationError(
                    'Number of selected `%s` nodes %s doesn\'t match the expected quant %s.' %
                    (self.name, filtered_num_nodes, self.quant.raw_quant))

        for node in nodes:
            if self.visible:
                if self.raw_value is not None:
                    extracted = node.select(self.compiled_value).extract()
                    if self.callback:
                        try:
                            if self.context_callback:
                                extracted = [self.callback(v, context=context) for v in extracted]
                            else:
                                extracted = [self.callback(v) for v in extracted]
                        except Exception as e:
                            raise SValidationError(
                                'Callback function returned an error on node `%s`: %s' %
                                (self.name, e))
                    result[self.name].extend(extracted)
                else:
                    if self.callback:
                        try:
                            if self.context_callback:
                                node = self.callback(node, context=context)
                            else:
                                node = self.callback(node)
                        except Exception as e:
                            raise SValidationError(
                                'Callback function returned an error on node `%s`: %s' %
                                (self.name, e))
                    result[self.name].append(node)

            if self.group is not None:
                groupd = defaultdict(list)
                for c in self.children:
                    for k, v in c._parse(node, context).iteritems():
                        groupd[k].extend(v)
                result[self.group].append(groupd)
            else:
                for c in self.children:
                    for k, v in c._parse(node, context).iteritems():
                        result[k].extend(v)
        return result

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

    @classmethod
    def absolute_url(cls, value, context):
        '''
        Useful callback method when parsing out urls.
        '''
        response = context['response']
        return urlparse.urljoin(response.base_url, value)
