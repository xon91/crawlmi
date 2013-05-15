from urlparse import urlparse

from crawlmi.extractor import IGNORED_EXTENSIONS
from crawlmi.utils.misc import arg_to_iter
from crawlmi.utils.python import to_str, unique_list, regex
from crawlmi.utils.url import is_url_from_any_domain, has_url_any_extension


_matches = lambda url, regexs: any((r.search(url) for r in regexs))


class BaseLinkExtractor(object):
    def __init__(self, allow=None, deny=None,
                 allow_domains=None, deny_domains=None,
                 tags=['a', 'area', 'link'], attrs=['href'], unique=True,
                 deny_extensions=None, filter_mobile=True):
        self.allow_res = [regex(x) for x in arg_to_iter(allow)]
        self.deny_res = [regex(x) for x in arg_to_iter(deny)]
        self.allow_domains = set(arg_to_iter(allow_domains))
        self.deny_domains = set(arg_to_iter(deny_domains))
        self.unique = unique
        if deny_extensions is None:
            deny_extensions = IGNORED_EXTENSIONS
        self.deny_extensions = set(['.' + e for e in deny_extensions])
        self.filter_mobile = filter_mobile

        tags = list(arg_to_iter(tags))  # make a local copy
        self.tag_func = lambda x: x in tags

        attrs = list(arg_to_iter(attrs))
        self.attr_func = lambda x: x in attrs

    def _extract_links(self, response):
        raise NotImplementedError

    def link_allowed(self, link):
        return self.url_allowed(link.url)

    def url_allowed(self, url):
        url = to_str(url)
        parsed_url = urlparse(url)
        allowed = parsed_url.scheme in ['http', 'https', 'file']
        # filter mobile and pda sites
        if allowed and self.filter_mobile:
            allowed &= not parsed_url.netloc.startswith('m.')
            allowed &= not parsed_url.netloc.startswith('pda.')
        if allowed and self.allow_res:
            allowed &= _matches(url, self.allow_res)
        if allowed and self.deny_res:
            allowed &= not _matches(url, self.deny_res)
        if allowed and self.allow_domains:
            allowed &= is_url_from_any_domain(parsed_url, self.allow_domains)
        if allowed and self.deny_domains:
            allowed &= not is_url_from_any_domain(parsed_url, self.deny_domains)
        if allowed and self.deny_extensions:
            allowed &= not has_url_any_extension(parsed_url, self.deny_extensions)
        return allowed

    def extract_links(self, response, process_links=None):
        '''
        Return the list of extracted links from the response body.
            link.url - string; url is escaped and ready to be visited
            link.text - unicode; text from inside the <a></a> tags
        '''

        links = self._extract_links(response)
        # filter bad links
        links = filter(self.link_allowed, links)
        # user process links
        if process_links is not None:
            links = filter(lambda x: x is not None, map(process_links, links))
        # uniquify links
        links = (unique_list(links, key=lambda link: link.url) if self.unique
                 else links)
        return links
