class Link(object):
    __slots__ = ['url', 'text', 'nofollow']

    def __init__(self, url, text='', nofollow=False):
        self.url = url
        self.text = text
        self.nofollow = nofollow

    def __eq__(self, other):
        return (self.url == other.url and self.text == other.text and
                self.nofollow == other.nofollow)

    def __hash__(self):
        return hash(self.url) ^ hash(self.text) ^ hash(self.nofollow)

    def __repr__(self):
        return 'Link(url=%r, text=%r, nofollow=%r)' % (self.url, self.text,
                                                       self.nofollow)
